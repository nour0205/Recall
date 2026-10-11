from app.rag.hybrid_retriever import hybrid_retrieve
from app.orchestration.registry import normalize_document_id


def retrieve_for_document(
    store,
    question: str,
    document_id: str,
    k: int = 4,
    retrieve_k: int = 10
):
    resolved_id = normalize_document_id(document_id)
    where = {"document_id": resolved_id}


    candidates = hybrid_retrieve(
        store=store,
        question=question,
        k=k,
        where=where,
        candidate_k=retrieve_k,
    )

    items = candidates

    normalized = []
    for item in items:
        text = item.text.strip()
        if not text:
            continue

        item_copy = item.model_dump()
        item_copy["text"] = text
        normalized.append(item_copy)

    return normalized
