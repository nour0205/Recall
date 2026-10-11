from app.llm.client import chat
from app.rag.hybrid_retriever import hybrid_retrieve
from app.orchestration.prompts import build_answer_prompt, normalize_answer
from types import SimpleNamespace
from app.schemas.api import SourceItem, RagAnswerResult


def build_rag_prompt(question: str, contexts: list[str]) -> list[dict]:
    return build_answer_prompt(question, [SimpleNamespace(document_id="context", text=t) for t in contexts], "unknown")


def rag_answer_with_store(
    question: str,
    store,
    k: int = 4,
    where: dict | None = None,
    retrieve_k: int = 10
) -> str:
    candidates = hybrid_retrieve(
        store=store,
        question=question,
        k=k,
        where=where,
        candidate_k=retrieve_k,
    )

    items = [item for item in candidates if item.text.strip()]

    contexts = [item.text for item in items if item.text.strip()]

    if not contexts:
        return "I don't know."

    messages = build_answer_prompt(question, items, "unknown")
    return normalize_answer(chat(messages))


def rag_answer_with_sources(
    question: str,
    store,
    k: int = 4,
    where: dict | None = None,
    retrieve_k: int = 10
) -> RagAnswerResult:
    candidates = hybrid_retrieve(
        store=store,
        question=question,
        k=k,
        where=where,
        candidate_k=retrieve_k,
    )

    items = [item for item in candidates if item.text.strip()]

    contexts = [item.text for item in items if item.text.strip()]

    if not contexts:
        return RagAnswerResult(
            answer="I don't know.",
            sources=[]
        )

    messages = build_answer_prompt(question, items, "unknown")
    answer = normalize_answer(chat(messages))

    if answer.strip() == "I don't know.":
        return RagAnswerResult(
            answer=answer,
            sources=[]
        )

    sources = [
        SourceItem(
            document_id=item.document_id,
            chunk_index=item.chunk_index,
            text=item.text,
            retrieval_type=item.retrieval_type,
            hybrid_score=item.hybrid_score,
            rerank_score=getattr(item, "rerank_score", None),
        )
        for item in items
    ]

    return RagAnswerResult(
        answer=answer,
        sources=sources
    )
