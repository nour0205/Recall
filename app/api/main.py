from collections import defaultdict
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import APIError

# ---- Core RAG imports ----
from app.embeddings.embedder import embed_texts
from app.vectordb.chroma_store import ChromaStore
from app.rag.hybrid_retriever import hybrid_retrieve
from app.llm.client import chat
from app.library import IngestionError, add_document, delete_document as remove_document

# ---- Orchestration imports ----
from app.orchestration.prompts import build_answer_prompt, normalize_answer, REFUSAL
from app.orchestration.utils import build_study_hint

# ---- Schema imports ----
from app.schemas.api import (
    AnswerResponse,
    IngestRequest,
    QuestionRequest,
    SourceItem,
)


# -------------------------------------------------------------------
# App + Store
# -------------------------------------------------------------------
logger = logging.getLogger(__name__)
app = FastAPI(title="Recall API", version="3.0")
store = ChromaStore(collection_name="api-demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def build_where_clause(req: QuestionRequest):
    clauses = []
    if req.document_id:
        clauses.append({"document_id": req.document_id})
    elif req.document_ids:
        clauses.append({"document_id": {"$in": list(dict.fromkeys(req.document_ids))}})
    if req.owner:
        clauses.append({"owner": req.owner})
    return {"$and": clauses} if len(clauses) > 1 else (clauses[0] if clauses else None)


def to_source_items(items):
    return [
        SourceItem(
            document_id=item.document_id,
            chunk_index=item.chunk_index,
            text=item.text,
            retrieval_type=item.retrieval_type,
            hybrid_score=getattr(item, "hybrid_score", None),
            rerank_score=getattr(item, "rerank_score", None),
        )
        for item in items
    ]


# -------------------------------------------------------------------
# ASK
# -------------------------------------------------------------------
# No intent planner: an ablation showed it never changed the answer prompt
# while adding ~40% latency (evaluation/PLANNER_ABLATION.md). `route` stays
# in the response schema for compatibility and is always None.
@app.post("/ask", response_model=AnswerResponse)
def ask(req: QuestionRequest):
    where = build_where_clause(req)

    # 1. Hybrid retrieval. Keep RRF chunk order, including complementary
    #    chunks from one document.
    results = hybrid_retrieve(
        store=store,
        question=req.question,
        k=5,
        where=where,
        candidate_k=10,
    )
    results = [r for r in results if r.text.strip()]
    if not results:
        return AnswerResponse(answer=REFUSAL, route=None, sources=[], study_hint=None)

    # 2. Grounded generation. A refusal is a valid result, not an error.
    #    The OpenAI client already retries transient failures (2 retries with
    #    backoff), so an APIError here is an outage: report it, don't hide it.
    try:
        answer = normalize_answer(chat(build_answer_prompt(question=req.question, sources=results, route=None)))
    except APIError as exc:
        logger.warning("Answer model unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="The answer model is unavailable. Please try again.") from exc

    if answer == REFUSAL:
        return AnswerResponse(answer=REFUSAL, route=None, sources=[], study_hint=None)
    sources = to_source_items(results)
    return AnswerResponse(answer=answer, route=None, sources=sources, study_hint=build_study_hint(None, sources))


# -------------------------------------------------------------------
# INGEST
# -------------------------------------------------------------------
@app.post("/ingest")
def ingest(req: IngestRequest):
    try:
        return add_document(store, req, embed=embed_texts)
    except IngestionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# -------------------------------------------------------------------
# DEBUG
# -------------------------------------------------------------------
@app.post("/debug/retrieve")
def debug_retrieve(req: QuestionRequest):
    where = build_where_clause(req)

    results = hybrid_retrieve(
        store=store,
        question=req.question,
        k=5,
        where=where,
    )

    return {"results": [r.model_dump() for r in results]}


# -------------------------------------------------------------------
# DOCUMENT LIST
# -------------------------------------------------------------------
@app.get("/documents")
def list_documents():
    data = store.collection.get(include=["metadatas", "documents"])

    grouped = defaultdict(
        lambda: {
            "document_id": None,
            "chunks": 0,
            "preview": None,
        }
    )

    metadatas = data.get("metadatas") or []
    documents = data.get("documents") or []

    for meta, doc in zip(metadatas, documents):
        if meta is None or doc is None:
            continue

        doc_id = meta.get("document_id")
        if not doc_id:
            continue

        entry = grouped[doc_id]
        entry["document_id"] = doc_id
        entry["chunks"] += 1

        if not entry["preview"]:
            entry["preview"] = doc[:200]

    return {"documents": list(grouped.values())}

@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    deleted = remove_document(store, document_id)
    if not any(deleted.values()):
        raise HTTPException(status_code=404, detail=f"No note named '{document_id}'.")
    return {"status": "deleted", "document_id": document_id, **deleted}
