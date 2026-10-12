from app.rag.hybrid_retriever import hybrid_retrieve


def retrieve_for_document(
    store,
    question: str,
    document_id: str,
    k: int = 4,
    retrieve_k: int = 10
):
    where = {"document_id": document_id}

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
