from typing import Any, Literal

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    id: str
    document_id: str
    chunk_id: str | None = None
    chunk_index: int | None = None
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    retrieval_type: Literal["vector", "bm25", "hybrid", "unknown"] = "unknown"
    score: float | None = None
    bm25_score: float | None = None
    hybrid_score: float | None = None
    rank: int | None = None
    found_by_vector: bool = False
    found_by_bm25: bool = False


class RankedChunk(RetrievedChunk):
    rerank_score: float
