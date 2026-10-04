"""Controlled retrieval configurations; no generation or production routing."""

from typing import Literal

from app.rag.hybrid_retriever import (
    reciprocal_rank_fusion,
    retrieve_bm25_candidates,
    retrieve_vector_candidates,
    to_retrieved_chunk,
)
from app.rag.reranker import rerank_items
from app.schemas.retrieval import RankedChunk, RetrievedChunk

RetrievalMode = Literal["vector", "bm25", "hybrid", "hybrid_reranked"]


def retrieve(
    store,
    question: str,
    mode: RetrievalMode = "vector",
    k: int = 5,
    candidate_k: int | None = None,
    where: dict | None = None,
) -> list[RetrievedChunk] | list[RankedChunk]:
    """Retrieve at most k chunks, using candidate_k results per search backend.

    candidate_k defaults to k and must be at least k. Both hybrid modes fuse
    the same full candidate union before truncation or heuristic reranking.
    List order is the final ranking; rank retains its backend input meaning.
    Scores retain existing meanings (vector distance, Whoosh score, RRF score).
    Whoosh filters after top-k search, as in production. Legacy chunks lacking
    chunk_id retain the production document_id:chunk_index identity fallback.
    """
    if mode not in ("vector", "bm25", "hybrid", "hybrid_reranked"):
        raise ValueError(f"Unknown retrieval mode: {mode}")
    depth = k if candidate_k is None else candidate_k
    if k < 1 or depth < k:
        raise ValueError("k must be positive and candidate_k must be at least k")

    if mode == "vector":
        rows = retrieve_vector_candidates(store, question, k=depth, where=where)
        return [
            to_retrieved_chunk({**row, "found_by_vector": True})
            for row in rows[:k]
        ]
    if mode == "bm25":
        rows = retrieve_bm25_candidates(question, k=depth, where=where)
        return [
            to_retrieved_chunk({**row, "found_by_bm25": True})
            for row in rows[:k]
        ]

    vector_rows = retrieve_vector_candidates(store, question, k=depth, where=where)
    bm25_rows = retrieve_bm25_candidates(question, k=depth, where=where)
    candidates = reciprocal_rank_fusion(vector_rows, bm25_rows)
    if mode == "hybrid_reranked":
        return rerank_items(question, candidates, k=k)
    return candidates[:k]
