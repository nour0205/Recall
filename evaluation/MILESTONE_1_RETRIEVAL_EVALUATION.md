# Milestone 1: Retrieval Evaluation & Benchmarking

Completed 2026-10-04. Scope: retrieval quality and controlled reranker experiments;
generation quality has not been evaluated.

## Objective and architecture

Evaluate Recall retrieval with labeled evidence and controlled comparisons,
rather than assume that hybrid retrieval or reranking improves results. Compare
vector-only, BM25-only, hybrid/RRF, hybrid with the existing heuristic, and hybrid
with a local MiniLM cross-encoder.

The retrieval stack uses OpenAI `text-embedding-3-small` embeddings, persisted
Chroma `api-demo` dense retrieval, Whoosh BM25 sparse retrieval, and Reciprocal
Rank Fusion (RRF). Optional rerankers reorder fused candidates.

Production callers continue to call `hybrid_retrieve()` directly. It retrieves
up to `k` candidates per backend, fuses them, and returns at most `k` chunks.
Routed `/ask` uses the first three hybrid retrieval results. The fallback generation
path retains the existing lexical heuristic reranker, as do other existing paths.
This milestone's preferred
baseline is an evaluation decision, not a production rollout.

Evaluation-only code under `evaluation/` exposes distinct retrieval modes and
uses `candidate_k=10` per backend and final `k=5`. Paired reranker experiments
retrieve one full RRF union per query and apply each ordering to that same pool
before selecting five results. The MiniLM run's unions contained 10–16 chunks;
they were not truncated to ten. Metadata and chunk UUIDs are preserved.

Changes made during the milestone: reusable candidate helpers and metadata
preservation, offline retrieval modes, benchmark validation, pure metrics,
experiment/report scripts, a Whoosh free-text query fix, and an evaluation-only
semantic reranker with separately pinned dependencies. RRF and heuristic scoring
were not tuned. No endpoint redesign or generation evaluation was implemented.

## Benchmark evolution

The initial five-case pilot had four answerable cases and one unanswerable case.
After the Whoosh fix, all four retrieval modes had identical measured quality;
the pilot was too easy to distinguish them.

The expanded benchmark contains 19 manually curated questions: 16 answerable and
three unanswerable (005, 019, 020). Case 018 was dropped. Labels came from corpus
text, not retrieval rankings.

- [v1](benchmarks/retrieval_v1.json) scores the minimum canonical chunk UUIDs
  needed for each question. Equivalent overlapping alternatives remain in notes.
- [v2](benchmarks/retrieval_v2.json) preserves those questions and legacy labels
  and adds required evidence groups. Alternatives are OR within a group;
  complete evidence coverage requires all groups. One chunk may satisfy multiple
  groups. Only chunks fully supplying a named requirement are acceptable.

Evidence groups were introduced because equivalent overlapping chunks could
answer a question while missing an arbitrary canonical UUID. Counting every
overlapping copy as independently required would also distort recall. V1 remains
unchanged for reproducibility; v2 uses binary manual judgments, without semantic
label matching, graded relevance, or LLM judging.

## Metrics and experimental semantics

All quality aggregates macro-average the 16 answerable cases. Unanswerable
rankings are retained for inspection, not treated as evidence of refusal quality.
K is a positive integer. Duplicate retrieved IDs retain positions but do not
increase relevance or group coverage.

| Metric | Definition |
|---|---|
| Canonical Hit@K | 1 if any canonical relevant chunk is in the first K positions; otherwise 0. |
| Canonical Recall@K | Unique canonical relevant IDs found in top K / total unique canonical relevant IDs. |
| Canonical RR / MRR | Reciprocal of the first canonical hit's rank; 0 if absent. MRR averages RR across cases. |
| Evidence Hit@K | 1 if top K satisfies at least one required evidence group; otherwise 0. |
| Evidence Recall@K | Satisfied groups / total required groups. |
| Evidence RR / MRR | Reciprocal of the first rank satisfying any group; 0 if absent. MRR averages RR across cases. |
| Complete evidence coverage@K | Per-case 1 if all groups are satisfied in top K; otherwise 0. The rate averages these indicators. |

With no relevant items/groups, Hit and RR are 0 and Recall is undefined (`None`).
Complete evidence coverage is also undefined for unanswerable cases. Hit and RR
do not establish complete multi-part coverage. Reported RR/MRR use final top-five
outputs; the reranker rank-change analyses separately inspect the full pool.

## Major findings

### A. BM25 diagnosis

The initial BM25 run returned no hits for every full benchmark question. Direct
index inspection and simpler searches established that searchable terms existed.
The failure was natural-language input being interpreted as Whoosh query syntax:
default AND grouping, stopwords surviving in ID fields, and punctuation/wildcard
interpretation suppressed valid matches.

`search_whoosh()` now analyzes free text with the existing content analyzer,
constructs literal term queries across the intended fields, and combines them
with OR. The index and schema were not rebuilt. The pre-fix run demonstrates an
input-handling defect, not inherent BM25 weakness. This production helper fix
intentionally changes lexical results; `/ask` endpoint code was not changed by
the fix.

### B. Canonical 19-case comparison

Source: [four-mode run](results/retrieval_v1_20261003T204707249551Z.json).
Values below are exact terminating decimals; repeating MRR values include their
exact fractions.

| Mode | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| Vector | 0.75 | 1.0 | 1.0 | 0.6875 | 1.0 | 1.0 | 41/48 = 0.854166666666… |
| BM25 | 0.75 | 0.875 | 0.9375 | 0.6875 | 0.84375 | 0.9375 | 391/480 = 0.814583333333… |
| Hybrid/RRF | 0.6875 | 0.9375 | 0.9375 | 0.625 | 0.90625 | 0.9375 | 77/96 = 0.802083333333… |
| Hybrid + heuristic | 0.5 | 0.875 | 0.9375 | 0.4375 | 0.84375 | 0.9375 | 133/192 = 0.692708333333… |

Vector led this canonical comparison. These results do not establish hybrid
superiority over vector-only; canonical artifacts and the small corpus limit
that comparison. V2 rescoring covers the three shared-pool orderings, not a new
evidence-based vector/BM25 comparison.

### C. Heuristic reranker ablation

On the same full hybrid pool, earliest canonical rank improved on **0**, remained
unchanged on **10**, and worsened on **6** answerable queries. MRR fell from
77/96 (approximately **0.8021**) to 133/192 (approximately **0.6927**).

The score decomposition showed harmful promotions from incidental lexical token
overlap, including generic words and repeated query tokens. Some demotions were
canonical-versus-equivalent artifacts, but others promoted chunks lacking the
requested evidence. No heuristic tuning followed.

The full-pool counts include case 012 moving from rank 9 to 10; both positions
are outside final K=5. Final-five outcome counts are 0 improved / 11 unchanged /
5 worsened. Case 014 improves one complementary canonical chunk from 3 to 2
while its earliest canonical rank stays 1.

### D. MiniLM semantic reranker

`cross-encoder/ms-marco-MiniLM-L6-v2` scores question–passage pairs, with no RRF
score blending or thresholds. CPU FP32 inference uses stable RRF-order ties.
Earliest canonical rank improved on **2**, stayed unchanged on **10**, and
worsened on **4** answerable cases. Canonical MRR was **19/24 =
0.791666666666…**: better than the heuristic, slightly below plain hybrid.

Mean semantic reranking latency was **0.6489641263308984 seconds** over 19 queries
(approximately 0.65 s). Loading/download (**37.29058629996143 s**) and warmup
(**0.08571499993558973 s**) were measured separately. No input pairs were
truncated. This single CPU run does not establish production latency.

### E. Evidence-group rescoring

Saved rankings from the MiniLM experiment were rescored without retrieval or
reranking. Canonical scores were verified against the saved source results.

| Evidence metric | Hybrid/RRF | Heuristic | MiniLM |
|---|---:|---:|---:|
| Hit@1 | 0.9375 | 0.875 | 0.9375 |
| Hit@3 / Hit@5 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| Recall@1 | 0.875 | 0.8125 | 0.875 |
| Recall@3 | 0.96875 | 0.96875 | 1.0 |
| Recall@5 | 1.0 | 1.0 | 1.0 |
| MRR | **0.96875** | **0.93750** | **23/24 = 0.958333333333…** |
| Complete coverage@1 | 0.8125 | 0.75 | 0.8125 |
| Complete coverage@3 | **0.93750** | 0.93750 | **1.00000** |
| Complete coverage@5 | **1.00000** | **1.00000** | **1.00000** |

Evidence scoring changes interpretation on 002, 003, 008, 009, 011, 012, 015,
and 016. Equivalent evidence removes several canonical penalties. The remaining
hybrid/MiniLM quality differences are case 010 (hybrid finds evidence at rank 2,
MiniLM at 3) and case 015 (MiniLM completes both requirements by rank 3, hybrid
by rank 4). Neither ordering dominates every quality metric.

## Engineering decision

Plain hybrid/RRF is the preferred retrieval baseline for now: it provides the
best simplicity / quality / latency tradeoff for the evaluated shared-pool
options on this benchmark. Do not select the heuristic reranker. MiniLM remains
an evaluated experimental option, but its isolated top-three coverage gain is
insufficient to justify added CPU inference latency at this stage. This is not
a claim of universal hybrid superiority or a production behavior change.

## Limitations

- Only 19 manually curated questions, tied to the current corpus.
- Chroma contains only 27 chunks across 12 documents.
- Ingestion overlap creates repeated evidence and affects both ranking and labels.
- Whoosh contains 28 chunks, including an extra `ml` chunk absent from Chroma;
  the stale document catalog is not ground truth. The mismatch remains unresolved.
- One semantic reranking run; no uncertainty estimates or repeated-run study.
- Latencies are local measurements, not production benchmarks or a load test.
- No generation correctness, faithfulness, citation, or refusal evaluation yet.

## Reproducibility

Benchmarks and annotation rules: [v1](benchmarks/retrieval_v1.json),
[v2](benchmarks/retrieval_v2.json), [README](benchmarks/README.md).

| Artifact | Saved files |
|---|---|
| Pre-fix pilot | [JSON](results/retrieval_v1_20261003T191144327644Z.json) |
| Post-fix pilot | [JSON](results/retrieval_v1_20261003T202351628580Z.json) |
| Final canonical four-mode run | [JSON](results/retrieval_v1_20261003T204707249551Z.json), [Markdown](results/retrieval_v1_20261003T204707249551Z.md) |
| Failure analysis | [JSON](results/retrieval_v1_20261003T204707249551Z_failure_analysis.json), [Markdown](results/retrieval_v1_20261003T204707249551Z_failure_analysis.md) |
| Shared-pool heuristic ablation | [JSON](results/reranker_ablation_20261003T210540073940Z.json), [Markdown](results/reranker_ablation_20261003T210540073940Z.md) |
| Shared-pool MiniLM experiment | [JSON](results/semantic_ablation_20261004T092737920669Z.json), [Markdown](results/semantic_ablation_20261004T092737920669Z.md) |
| V2 evidence rescoring | [JSON](results/evidence_rescore_20261004T100113793072Z.json), [Markdown](results/evidence_rescore_20261004T100113793072Z.md) |

Key code: [retrieval abstraction](retrieval.py), [benchmark validation](benchmark.py),
[canonical metrics](metrics.py), [evidence metrics](evidence_metrics.py),
[semantic scorer](semantic_reranker.py), and [pinned evaluation dependencies](requirements.txt).
Runners, from repository root:

```text
python -m evaluation.run_retrieval_benchmark
python -m evaluation.run_reranker_ablation
python -m evaluation.run_semantic_ablation
python -m evaluation.rescore_evidence
```

The first three perform new retrieval experiments; evidence rescoring reads
saved rankings and checks corpus references without searching. Saved reports
are the historical evidence, not a guarantee that later reruns are identical.
Re-ingestion changes UUIDs. V2 rescoring records source/benchmark SHA256 hashes.
Earlier pilot labels differ from final v1 and must not be compared as unchanged
gold labels.

MiniLM revision: `233902d25c440f23af6f7d6e94d2946bac0bee0a`.
Runtime: sentence-transformers **5.1.2**, transformers **4.57.1**, torch
**2.9.0+cpu**, CPU FP32, batch size **16**, maximum pair length **512**.
Evaluation ML dependencies are separate from production requirements.

Final verification on 2026-10-04: `python -m unittest discover -s tests`:

```text
Ran 61 tests in 0.115s
OK
```

The verification used Python 3.12.13 with the core dependencies. Use an activated
environment with the root requirements to run the command above. Tests use fake
semantic scorers and do not download the model. This closeout adds documentation only; no experiments,
generation calls, retrieval changes, or production rollout were performed.
