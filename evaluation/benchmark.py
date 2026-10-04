"""Benchmark schemas and supplied-inventory checks; no corpus access or metrics."""

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonEmptyString = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
QuestionCategory = Literal[
    "factual", "conceptual", "comparison", "multi_part", "out_of_scope"
]


class BenchmarkModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RelevantChunk(BenchmarkModel):
    chunk_id: NonEmptyString
    document_id: NonEmptyString
    # Omission represents binary relevance. Reserved for future graded labels.
    relevance: Annotated[int, Field(ge=1, le=2)] | None = None


class BenchmarkCase(BenchmarkModel):
    question_id: NonEmptyString
    question: NonEmptyString
    category: QuestionCategory
    answerable: bool
    relevant_document_ids: list[NonEmptyString]
    relevant_chunks: list[RelevantChunk]
    notes: str | None = None

    @model_validator(mode="after")
    def check_relevance(self) -> Self:
        documents = self.relevant_document_ids
        chunk_ids = [chunk.chunk_id for chunk in self.relevant_chunks]
        if len(documents) != len(set(documents)):
            raise ValueError("relevant_document_ids must be unique")
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("relevant_chunks must have unique chunk IDs")
        if self.answerable and not self.relevant_chunks:
            raise ValueError("answerable cases must have relevant chunks")
        if not self.answerable and (documents or self.relevant_chunks):
            raise ValueError("unanswerable cases must have empty relevance lists")
        if set(documents) != {chunk.document_id for chunk in self.relevant_chunks}:
            raise ValueError("relevant_document_ids must match the documents of relevant_chunks")
        return self


class BenchmarkCorpus(BenchmarkModel):
    collection_name: NonEmptyString


class Benchmark(BenchmarkModel):
    schema_version: Annotated[int, Field(ge=1, le=1)]
    corpus: BenchmarkCorpus
    cases: list[BenchmarkCase]

    @model_validator(mode="after")
    def check_question_ids(self) -> Self:
        question_ids = [case.question_id for case in self.cases]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("question IDs must be unique across the benchmark")
        return self


class AcceptableChunk(BenchmarkModel):
    document_id: NonEmptyString
    chunk_id: NonEmptyString


class EvidenceGroup(BenchmarkModel):
    group_id: NonEmptyString
    requirement: NonEmptyString
    acceptable_chunks: Annotated[list[AcceptableChunk], Field(min_length=1)]

    @model_validator(mode="after")
    def unique_chunks(self) -> Self:
        ids = [c.chunk_id for c in self.acceptable_chunks]
        if len(ids) != len(set(ids)):
            raise ValueError("chunk IDs must be unique within an evidence group")
        return self


class EvidenceBenchmarkCase(BenchmarkCase):
    evidence_groups: list[EvidenceGroup]

    @model_validator(mode="after")
    def check_groups(self) -> Self:
        if any(c.relevance is not None for c in self.relevant_chunks):
            raise ValueError("benchmark v2 uses binary evidence; graded legacy labels are not supported")
        ids = [g.group_id for g in self.evidence_groups]
        if len(ids) != len(set(ids)):
            raise ValueError("group IDs must be unique per case")
        if self.answerable != bool(self.evidence_groups):
            raise ValueError("answerable cases require groups; unanswerable cases require no groups")
        ownership = {c.chunk_id: c.document_id for c in self.relevant_chunks}
        for group in self.evidence_groups:
            for chunk in group.acceptable_chunks:
                if chunk.chunk_id in ownership and ownership[chunk.chunk_id] != chunk.document_id:
                    raise ValueError("inconsistent document assignment for chunk ID")
                ownership[chunk.chunk_id] = chunk.document_id
        return self


class EvidenceBenchmark(Benchmark):
    schema_version: Annotated[int, Field(ge=2, le=2)]
    cases: list[EvidenceBenchmarkCase]


def load_benchmark(path: str | Path) -> Benchmark | EvidenceBenchmark:
    """Read UTF-8 JSON and validate its structure, without opening any indexes."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    model = EvidenceBenchmark if data.get("schema_version") == 2 else Benchmark
    return model.model_validate(data)


def validate_corpus(
    benchmark: Benchmark | EvidenceBenchmark,
    inventories: Mapping[str, Mapping[str, str]],
) -> list[str]:
    """Return corpus issues using named inventories of chunk_id -> document_id.

    Supply inventories from the intended collection/index, including all live
    chunks. Each legacy and evidence-group reference is checked in every inventory. When multiple
    inventories are supplied, their full membership and assignments are also
    compared, even if the benchmark has no cases. No data is read or changed.
    An empty issue list means validation passed against the supplied inventories;
    it does not establish that their contents or collection selection are current.
    """
    if not inventories:
        raise ValueError("Supply at least one corpus inventory")

    issues = []
    for case in benchmark.cases:
        references = list(case.relevant_chunks)
        for group in getattr(case, "evidence_groups", []):
            references.extend(group.acceptable_chunks)
        for chunk in references:
            for name, inventory in inventories.items():
                if chunk.chunk_id not in inventory:
                    issues.append(f"{case.question_id}: chunk {chunk.chunk_id} missing from {name}")
                elif inventory[chunk.chunk_id] != chunk.document_id:
                    issues.append(
                        f"{case.question_id}: chunk {chunk.chunk_id} belongs to "
                        f"{inventory[chunk.chunk_id]} in {name}, expected {chunk.document_id}"
                    )

    names = list(inventories)
    reference_name = names[0]
    reference = inventories[reference_name]
    for name in names[1:]:
        inventory = inventories[name]
        for chunk_id in sorted(reference.keys() - inventory.keys()):
            issues.append(f"Corpus mismatch: chunk {chunk_id} present in {reference_name}, missing from {name}")
        for chunk_id in sorted(inventory.keys() - reference.keys()):
            issues.append(f"Corpus mismatch: chunk {chunk_id} present in {name}, missing from {reference_name}")
        for chunk_id in sorted(reference.keys() & inventory.keys()):
            if reference[chunk_id] != inventory[chunk_id]:
                issues.append(
                    f"Corpus mismatch: chunk {chunk_id} belongs to {reference[chunk_id]} "
                    f"in {reference_name}, but {inventory[chunk_id]} in {name}"
                )
    return issues
