"""Pure chunk-ID retrieval metrics for a single query.

Relevant IDs are treated as a set. Retrieved duplicates retain their original
positions for cutoffs and ranks, but cannot increase the number of relevant hits.
Empty relevance sets yield hit=0.0, recall=None (undefined), and reciprocal rank=0.0.
"""

from collections.abc import Iterable, Sequence


def _validate_k(k: int) -> None:
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer")


def hit_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Return 1.0 if any of the first k results is relevant, otherwise 0.0."""
    _validate_k(k)
    relevant = set(relevant_ids)
    return float(any(chunk_id in relevant for chunk_id in retrieved_ids[:k]))


def recall_at_k(
    retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int
) -> float | None:
    """Return the fraction of unique relevant IDs in the first k results.

    Return None if there are no relevant IDs, because recall is undefined.
    """
    _validate_k(k)
    relevant = set(relevant_ids)
    if not relevant:
        return None
    return len(set(retrieved_ids[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved_ids: Sequence[str], relevant_ids: Iterable[str]) -> float:
    """Return 1 / first relevant rank (one-based), or 0.0 if no hit exists."""
    relevant = set(relevant_ids)
    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant:
            return 1.0 / rank
    return 0.0
