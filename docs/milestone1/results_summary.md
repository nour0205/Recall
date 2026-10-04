# Milestone 1: approved public results

Use these as corpus-specific pilot results, not claims of universal superiority.
All quality averages below use the 16 answerable cases. Values are rounded only
where indicated. Full methodology: [Milestone report](../../evaluation/MILESTONE_1_RETRIEVAL_EVALUATION.md).

## Benchmark

**19 questions: 16 answerable, 3 unanswerable.**
Sources: [v1](../../evaluation/benchmarks/retrieval_v1.json),
[v2](../../evaluation/benchmarks/retrieval_v2.json).
V1 uses canonical UUIDs; v2 uses required evidence groups with acceptable
alternatives. Cases 005, 019, and 020 are unanswerable.

## Heuristic ablation — canonical scoring

- Earliest canonical rank: **0 improved / 10 unchanged / 6 worsened**.
- Hybrid MRR before reranking: **0.802083** (rounded from 77/96).
- Heuristic MRR: **0.692708** (rounded from 133/192).

Source: [heuristic ablation JSON](../../evaluation/results/reranker_ablation_20261003T210540073940Z.json),
`aggregates.rank_change`, `aggregates.hybrid.mrr`, and `aggregates.hybrid_reranked.mrr`.
These counts inspect earliest canonical rank in the full pool, not just top five.
The [canonical four-mode JSON](../../evaluation/results/retrieval_v1_20261003T204707249551Z.json)
independently records the same two MRR values under `aggregates.<mode>.metrics.mrr`.

## MiniLM experiment — canonical scoring and latency

- Earliest canonical rank: **2 improved / 10 unchanged / 4 worsened**.
- Mean semantic reranking latency: **approximately 0.649 s on CPU**
  (measured value: 0.6489641263308984 s across all 19 queries).
- Experimental latency measurement, **not a production benchmark**; model
  loading/download and warmup are excluded.

Source: [semantic ablation JSON](../../evaluation/results/semantic_ablation_20261004T092737920669Z.json),
`aggregates.semantic_rank_change` and `aggregates.semantic_latency_seconds.mean`.
Runtime: MiniLM L6 v2, CPU FP32. The heuristic is lexical, not semantic.

## Final evidence-group scoring

| Ordering | Evidence MRR | Complete coverage@3 | Complete coverage@5 |
|---|---:|---:|---:|
| Hybrid / RRF | **0.96875** | **0.93750** | **1.00000** |
| Heuristic | **0.93750** | **0.93750** | **1.00000** |
| MiniLM | **0.95833** | **1.00000** | **1.00000** |

Source: [evidence rescoring JSON](../../evaluation/results/evidence_rescore_20261004T100113793072Z.json),
`aggregates.<mode>.evidence.mrr`, `.complete_at_3`, and `.complete_at_5`.
MiniLM's exact MRR is 23/24 = 0.958333333333…; **0.95833** is rounded.
No new retrieval or model calls were made for rescoring.

Graphic rounding to three decimals: Hybrid **0.969**, MiniLM **0.958**,
Heuristic **0.938**. Canonical ablation MRR rounding: **0.802 → 0.693**.
Do not mix canonical MRR and evidence MRR as if they were the same metric.

## Defensible conclusion and limitations

Among the evaluated hybrid orderings, plain Vector + BM25 + RRF is currently
retained as the preferred baseline because it offers the best quality / simplicity /
latency trade-off on this benchmark. The heuristic was rejected as the preferred baseline.
MiniLM is an evaluated experimental option: one coverage improvement does not
currently justify added CPU latency. This decision is not a production rollout;
existing heuristic fallback code remains.

Only 19 manually curated questions and 27 Chroma chunks across 12 documents;
ingestion overlap; Whoosh has one extra chunk; one semantic experiment run;
local timing rather than a production load test. The original canonical test
favored vector-only, and evidence rescoring compares only the three hybrid
orderings. Do not claim hybrid beats vector-only universally. No generated-answer
correctness, faithfulness, or refusal evaluation has been performed.
