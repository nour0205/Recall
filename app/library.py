"""The notes library: keeps the vector index (Chroma) and the keyword index
(Whoosh BM25) in step.

Every chunk lives in both indexes under the same chunk ID. Adding a note is
all-or-nothing: chunks and embeddings are computed before anything is written,
and if either write fails, whatever was written is removed again. Deleting a
note removes it from both. check_consistency() reports chunks found in only
one index; repair() fixes them without any embedding calls.
"""
import uuid
from typing import Callable

from app.ingestion.chunker import apply_overlap, base_chunks
from app.schemas.api import IngestRequest
from app.utils.hash import hash_text
from app.vectordb.whoosh_index import (
    add_chunks_to_whoosh,
    delete_chunks_from_whoosh,
    delete_document_from_whoosh,
    whoosh_records,
)


class IngestionError(RuntimeError):
    """Raised after a failed ingestion has been rolled back."""


def _bm25_has_document(document_id: str) -> bool:
    return any(record.get("document_id") == document_id for record in whoosh_records())


def add_document(store, req: IngestRequest, embed: Callable[[list[str]], list] | None = None) -> dict:
    doc_hash = hash_text(req.text)
    if store.collection.get(where={"doc_hash": doc_hash}, limit=1)["ids"]:
        return {"status": "duplicate"}
    # A name in either index blocks reuse, so a half-written note is never extended.
    if store.collection.get(where={"document_id": req.document_id}, limit=1)["ids"] or _bm25_has_document(req.document_id):
        return {"status": "conflict"}

    chunks = apply_overlap(base_chunks(req.text), overlap=1)
    if not chunks:
        return {"status": "no content"}

    if embed is None:
        from app.embeddings.embedder import embed_texts as embed
    embeddings = embed(chunks)  # External call; nothing has been written yet.

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = []
    for i in range(len(chunks)):
        meta = {
            "chunk_id": ids[i],
            "document_id": req.document_id,
            "doc_hash": doc_hash,
            "chunk_index": i,
            "topic_tags": ", ".join(req.topic_tags) if req.topic_tags else "",
        }
        # Chroma rejects None metadata values, so optional fields are only set when present.
        for key in ("document_type", "course", "source", "owner"):
            if getattr(req, key):
                meta[key] = getattr(req, key)
        metadatas.append(meta)
    bm25_chunks = [
        {"chunk_id": ids[i], "document_id": req.document_id, "chunk_index": i, "text": chunks[i],
         "source": req.source or "", "owner": req.owner or ""}
        for i in range(len(chunks))
    ]

    try:
        store.add_texts(ids=ids, texts=chunks, embeddings=embeddings, metadatas=metadatas)
        add_chunks_to_whoosh(bm25_chunks)
    except Exception as exc:
        _roll_back(store, ids)
        raise IngestionError(f"Could not add '{req.document_id}'; no changes were kept.") from exc

    return {"status": "ingested", "chunks_added": len(chunks)}


def _roll_back(store, ids: list[str]) -> None:
    for undo in (lambda: store.collection.delete(ids=ids), lambda: delete_chunks_from_whoosh(ids)):
        try:
            undo()
        except Exception:
            pass  # Best effort; check_consistency() reports anything left behind.


def delete_document(store, document_id: str) -> dict:
    ids = store.collection.get(where={"document_id": document_id})["ids"]
    if ids:
        store.collection.delete(ids=ids)
    bm25_deleted = delete_document_from_whoosh(document_id)
    return {"vector_chunks_deleted": len(ids), "bm25_chunks_deleted": bm25_deleted}


def check_consistency(store) -> dict:
    vector = store.collection.get(include=["metadatas"])
    vector_ids = {cid: (meta or {}).get("document_id") for cid, meta in zip(vector["ids"], vector["metadatas"])}
    bm25_ids = {r["chunk_id"]: r.get("document_id") for r in whoosh_records()}
    only = lambda a, b: sorted(({"chunk_id": cid, "document_id": a[cid]} for cid in a.keys() - b.keys()),
                               key=lambda row: (str(row["document_id"]), row["chunk_id"]))
    vector_only, bm25_only = only(vector_ids, bm25_ids), only(bm25_ids, vector_ids)
    return {
        "vector_chunks": len(vector_ids),
        "bm25_chunks": len(bm25_ids),
        "vector_only": vector_only,
        "bm25_only": bm25_only,
        "consistent": not vector_only and not bm25_only,
    }


def repair(store) -> dict:
    """Make the keyword index match the vector index, which holds the embeddings."""
    report = check_consistency(store)
    removed = delete_chunks_from_whoosh([row["chunk_id"] for row in report["bm25_only"]]) if report["bm25_only"] else 0
    missing = [row["chunk_id"] for row in report["vector_only"]]
    if missing:
        records = store.collection.get(ids=missing, include=["documents", "metadatas"])
        add_chunks_to_whoosh([
            {"chunk_id": cid, "document_id": meta["document_id"], "chunk_index": meta.get("chunk_index", 0),
             "text": text, "source": meta.get("source", ""), "owner": meta.get("owner", "")}
            for cid, text, meta in zip(records["ids"], records["documents"], records["metadatas"])
        ])
    return {"bm25_orphans_removed": removed, "bm25_chunks_restored": len(missing)}
