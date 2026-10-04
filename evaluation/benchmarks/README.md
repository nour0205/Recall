# Retrieval benchmarks

## Benchmark v2: evidence requirements

`retrieval_v2.json` preserves the same 19 questions and all legacy metadata and
canonical labels from v1. It adds required `evidence_groups` and uses
`schema_version: 2`. Keep `retrieval_v1.json` unchanged for historical experiments.

Each group requires a unique per-case `group_id`, a nonblank `requirement`, and
a nonempty `acceptable_chunks` list of `{document_id, chunk_id}` references.
Chunk IDs are unique within a group but may appear in several groups. Every
reference must exist in the intended Chroma corpus with the specified document
ownership. Answerable cases require groups; unanswerable cases require `[]`.
No graded labels, semantic matching, or model judging are used.

Alternatives are OR within a group. Complete coverage requires all groups.
Accept a chunk only when it fully supplies the group's named requirement.
Partial material can satisfy a narrower requirement, but unrelated background
stays in notes. Evidence-group metrics use only the groups; legacy canonical
metrics continue using only `relevant_chunks`. `relevant_document_ids` still
describes the legacy labels, not the union of alternative documents.

`evaluation/evidence_metrics.py` accepts ranked chunk IDs and an iterable of
groups, each an iterable of acceptable chunk IDs. Evidence Hit@K means at least
one group is satisfied; Evidence Recall@K is the fraction of groups satisfied;
evidence reciprocal rank is the reciprocal of the first rank satisfying any
group. Neither Hit nor reciprocal rank guarantees complete multi-part evidence.
One chunk may satisfy multiple groups. Repeated retrieved IDs retain positions
but never increase coverage. K must be a positive integer. With no groups, Hit
and reciprocal rank are zero and Recall is undefined (`None`).

Complete evidence coverage at K is `1.0` when evidence recall equals one,
otherwise `0.0`; it is undefined for unanswerable cases. Dataset summaries
macro-average over answerable cases only, with equal weight per case.

Run `python -m evaluation.rescore_evidence` from the repository root to rescore
the saved MiniLM experiment's final top-five rankings. It validates v2 against
persisted Chroma, verifies source questions and canonical scores, and saves
JSON/Markdown reports with source and benchmark SHA256 hashes. It does not
perform retrieval or reranking. RR/MRR retain the source experiment's top-five
scope. Unanswerable outputs remain available separately.

## Benchmark v1: canonical chunks

`retrieval_v1.json` contains 19 manually curated cases (16 answerable and three
unanswerable) with binary canonical chunk
relevance. It evaluates retrieval only. The root `eval_cases.json`
remains separate: it contains legacy planner and answer/refusal smoke checks,
not chunk-level gold labels.

## Format

Use a pretty-printed UTF-8 JSON object with required `schema_version` (integer
`1`), `corpus.collection_name` (currently `api-demo`), and `cases` (a list).
JSON is convenient to edit and review for a small curated dataset; JSONL is
unnecessary at this size. Unknown fields and incorrect field types are rejected.

Each case requires:

| Field | Meaning |
| --- | --- |
| `question_id` | Unique nonblank string, stable even if the question wording changes. |
| `question` | Nonblank question text. |
| `category` | `factual`, `conceptual`, `comparison`, `multi_part`, or `out_of_scope`. Independent of production intent routes. |
| `answerable` | Boolean: the corpus contains sufficient evidence to answer the complete question. |
| `relevant_document_ids` | Unique document IDs, exactly matching the documents represented in `relevant_chunks`. |
| `relevant_chunks` | Unordered list of judgments, each with required nonblank `chunk_id` and `document_id`. Chunk IDs must be unique within a case. |

Optional `notes` records annotation rationale, ambiguity, or missing evidence.
Each chunk judgment may have an optional integer `relevance`: `1` for supporting
or partial evidence, `2` for direct evidence. **Do not populate grades in v1.**
Omitting `relevance` means binary relevant; it does not imply a numeric grade.
The schema reserves this field for future graded annotations.

## Annotation rules

Answerable cases must have at least one relevant chunk. Read the actual chunk
text before labeling it; IDs and previews alone do not establish relevance.
Label the minimum set of canonical chunks needed to represent the evidence for
the complete question. Prefer the most complete relevant passage; when passages
provide identical evidence, prefer the more focused passage rather than counting
overlapping copies separately. Choose representatives from corpus text, never
from retrieval results. Use multiple canonical chunks only for genuinely
complementary evidence required by the question, including separate parts of a
multi-part question. Cases 014 and 015 each require two chunks; every other
answerable case has one. Case 018 is reserved for a later ambiguity benchmark.

Benchmark v1 scores canonical evidence chunks; equivalent overlapping
alternatives are recorded for manual review but are not included in automatic
Recall@K/MRR scoring. All current ID-based metrics use only `relevant_chunks`.
Notes identify alternatives by exact UUID and distinguish full equivalent
evidence, component substitutes, and partial supporting evidence. Alternatives
must not be added to `relevant_chunks` or `relevant_document_ids`.

Retrieving equivalent evidence instead of its canonical UUID can therefore score
as a miss; use the notes during manual failure analysis. Hit@K and reciprocal
rank indicate the first canonical hit, not complete coverage of multi-part
questions. Earlier five-case result files retain the previous labels and should
not be directly compared as though they used this annotation policy.

Unanswerable cases require `answerable: false`, `relevant_document_ids: []`, and
`relevant_chunks: []`. Choose clearly unsupported questions for v1 and explain
missing evidence in notes. Empty labels do not require retrieval to return no
results. Category and answerability are separate; a factual question can also
be unanswerable.

Use exact persisted chunk UUIDs. Current ingestion stores the same UUID as the
Chroma record ID, metadata `chunk_id`, and Whoosh `chunk_id`. Do not invent IDs
or substitute chunk indices. Re-ingestion generates new UUIDs, so review labels
and rerun validation whenever the corpus changes. The collection name identifies
the target corpus but does not freeze a corpus snapshot.

## Validation

`evaluation.benchmark.load_benchmark(path)` validates schema and case consistency.
Corpus checking is separate and requires supplied inventories, each mapping
`chunk_id` to `document_id` for all live chunks in the intended collection/index:

```python
from evaluation.benchmark import load_benchmark, validate_corpus

benchmark = load_benchmark("evaluation/benchmarks/retrieval_v1.json")
# chroma_inventory and whoosh_inventory are supplied by the caller.
issues = validate_corpus(benchmark, {
    "chroma": chroma_inventory,
    "whoosh": whoosh_inventory,
})
if issues:
    raise ValueError("\n".join(issues))
```

Build inventories from persisted records, not search results or catalog previews.
For Chroma, use the intended existing collection's records and metadata
`chunk_id`/`document_id`; verify the record ID matches metadata `chunk_id`.
For Whoosh, use live stored fields `chunk_id`/`document_id`. Report missing IDs
or duplicate inventory IDs while constructing inventories rather than silently
overwriting them. Inventory construction and index access are not implemented
by these helpers.

The helper reports absent gold chunks and incorrect document assignments in each
supplied inventory. It also reports membership/assignment differences between
inventories, including for an empty benchmark. Treat reported issues as failed
corpus validation; never silently drop unresolved labels. Supplying only one
inventory cannot detect differences between indexes. Validation trusts the
caller to provide current inventories from the intended collection.

Run focused checks with `python -m unittest discover -s tests -p test_benchmark.py -v`.

## Known corpus caveat

At inspection for this milestone, Chroma `api-demo` contained 27 chunks across
12 documents; Whoosh contained 28 live chunks, including one absent from Chroma.
`data/document_catalog.json` listed 37 documents and 119 declared chunks. The
catalog is therefore not an authoritative chunk inventory, and the two search
backends do not currently contain identical corpora. Fair comparisons require
addressing this mismatch separately before accepting benchmark results. This
task only documents and detects inconsistencies; it does not repair indexes,
delete documents, or update the catalog.
