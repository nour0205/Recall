"""Pure binary evidence metrics. Groups are iterables of acceptable chunk IDs.

OR within each group; complete coverage requires every group. Duplicates retain
retrieved positions but never increase coverage. One chunk may satisfy many groups.
No groups: hit=0, recall=None, reciprocal rank=0. Groups must be nonempty.
"""
from collections.abc import Iterable, Sequence
from evaluation.metrics import _validate_k


def _groups(groups: Iterable[Iterable[str]]) -> list[set[str]]:
    result = [set(group) for group in groups]
    if any(not group for group in result):
        raise ValueError("Evidence groups must contain acceptable IDs")
    return result


def evidence_hit_at_k(retrieved_ids: Sequence[str], groups: Iterable[Iterable[str]], k: int) -> float:
    _validate_k(k)
    retrieved = set(retrieved_ids[:k])
    return float(any(retrieved & group for group in _groups(groups)))


def evidence_recall_at_k(retrieved_ids: Sequence[str], groups: Iterable[Iterable[str]], k: int) -> float | None:
    _validate_k(k)
    accepted = _groups(groups)
    if not accepted:
        return None
    retrieved = set(retrieved_ids[:k])
    return sum(bool(retrieved & group) for group in accepted) / len(accepted)


def evidence_reciprocal_rank(retrieved_ids: Sequence[str], groups: Iterable[Iterable[str]]) -> float:
    accepted = set().union(*_groups(groups))
    return next((1.0 / rank for rank, cid in enumerate(retrieved_ids, 1) if cid in accepted), 0.0)
