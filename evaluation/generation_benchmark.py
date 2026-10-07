"""Frozen generation references and deterministic pre-generation evidence checks.

This module never builds prompts, calls a model, or scores generated answers.
"""

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from evaluation.benchmark import BenchmarkModel, NonEmptyString, load_benchmark

REFERENCE_PATH = Path("evaluation/benchmarks/generation_reference_v1.json")
RETRIEVAL_PATH = Path("evaluation/benchmarks/retrieval_v2.json")
CASE_IDS = tuple(f"retrieval_{i:03}" for i in (*range(1, 18), 19, 20))
REFUSAL_IDS = {"retrieval_005", "retrieval_019", "retrieval_020"}


def canonical_hash(value) -> str:
    serialized = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RequiredPoint(BenchmarkModel):
    point_id: NonEmptyString
    text: NonEmptyString
    evidence_group_ids: list[NonEmptyString]
    # Narrow a group's alternatives only where the point needs explicit evidence.
    support_chunk_ids: list[NonEmptyString] | None = None


class CitationExpectation(BenchmarkModel):
    source_support_required: bool
    citation_required_for_factual_claims: bool


class GenerationReferenceCase(BenchmarkModel):
    question_id: NonEmptyString
    reference_answer: NonEmptyString
    expected_behavior: Literal["answer", "refuse"]
    required_points: list[RequiredPoint] = Field(min_length=1)
    forbidden_or_unsupported_points: list[NonEmptyString]
    citation_expectation: CitationExpectation
    review_notes: NonEmptyString

    @model_validator(mode="after")
    def unique_points(self):
        ids = [point.point_id for point in self.required_points]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate required-point ID")
        return self


class GenerationReferences(BenchmarkModel):
    schema_version: Literal[1]
    retrieval_benchmark: Literal["retrieval_v2.json"]
    retrieval_benchmark_sha256: NonEmptyString
    corpus: dict
    reference_policy: NonEmptyString
    rubric: dict
    cases: list[GenerationReferenceCase]


def load_generation_benchmark(reference_path=REFERENCE_PATH, retrieval_path=RETRIEVAL_PATH):
    references = GenerationReferences.model_validate_json(Path(reference_path).read_text(encoding="utf-8"))
    retrieval_path = Path(retrieval_path)
    benchmark = load_benchmark(retrieval_path)
    if references.retrieval_benchmark_sha256 != file_hash(retrieval_path):
        raise ValueError("Frozen retrieval benchmark hash mismatch")
    if tuple(case.question_id for case in references.cases) != CASE_IDS:
        raise ValueError("Generation references must contain the exact 19 v2 IDs in order")
    if tuple(case.question_id for case in benchmark.cases) != CASE_IDS:
        raise ValueError("Retrieval benchmark must contain the exact 19 v2 IDs in order")
    if references.corpus.get("collection_name") != benchmark.corpus.collection_name:
        raise ValueError("Corpus collection mismatch")
    dimensions = {"correctness", "groundedness", "completeness", "refusal_correctness", "citation_correctness"}
    if not dimensions <= references.rubric.keys() or not references.rubric.get("prompt_compliance", {}).get("optional"):
        raise ValueError("Separate rubric dimensions and optional prompt compliance are required")
    for reference, case in zip(references.cases, benchmark.cases):
        refusal = case.question_id in REFUSAL_IDS
        if reference.expected_behavior != ("refuse" if refusal else "answer") or case.answerable == refusal:
            raise ValueError("Refusal-case identity mismatch")
        groups = {group.group_id: group for group in case.evidence_groups}
        mapped = set()
        for point in reference.required_points:
            if len(point.evidence_group_ids) != len(set(point.evidence_group_ids)):
                raise ValueError("Duplicate evidence group mapping")
            if (not refusal and not point.evidence_group_ids) or (refusal and point.evidence_group_ids):
                raise ValueError("Factual points require groups; refusal points have no groups")
            if not set(point.evidence_group_ids) <= groups.keys():
                raise ValueError("Unknown evidence group")
            mapped.update(point.evidence_group_ids)
            if point.support_chunk_ids is not None:
                accepted = {chunk.chunk_id for gid in point.evidence_group_ids for chunk in groups[gid].acceptable_chunks}
                if not point.support_chunk_ids or not set(point.support_chunk_ids) <= accepted:
                    raise ValueError("Point support overrides must narrow existing group alternatives")
        if mapped != groups.keys():
            raise ValueError("Every evidence group must have a required point")
        citation = reference.citation_expectation
        if citation.source_support_required == refusal or citation.citation_required_for_factual_claims == refusal:
            raise ValueError("Citation expectations do not match expected behavior")
    return benchmark, references


def point_evidence(reference, case, chunks) -> list[dict]:
    """OR among alternatives, AND among mapped groups; no answer inspection.

Checks use frozen corpus identities validated by the live preflight. They are
evidence availability labels, not generated-answer quality scores. Refusal
points have no factual evidence requirement and therefore return null.
"""
    groups = {group.group_id: group for group in case.evidence_groups}
    records = {(chunk.document_id, chunk.chunk_id) for chunk in chunks}
    output = []
    for point in reference.required_points:
        matches = {}
        for gid in point.evidence_group_ids:
            matches[gid] = [chunk.chunk_id for chunk in groups[gid].acceptable_chunks
                            if (chunk.document_id, chunk.chunk_id) in records
                            and (point.support_chunk_ids is None or chunk.chunk_id in point.support_chunk_ids)]
        output.append({
            "point_id": point.point_id,
            "evidence_group_ids": point.evidence_group_ids,
            "sufficient_retrieved_evidence": all(bool(ids) for ids in matches.values()) if matches else None,
            "supporting_chunk_ids_by_group": matches,
            "method": "frozen_v2_evidence_group_membership_with_point_overrides" if matches else "not_applicable_refusal",
        })
    return output
