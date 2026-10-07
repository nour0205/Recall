# Generation Baseline v1 — Human-Reviewed Results

19 completed generations: 16 answerable cases and 3 refusal cases. All 16 answerable cases had sufficient retrieved evidence.

Finalized validation passed. Results use the supplied human labels exactly; no LLM judge, RAGAS, or weighted overall score.

[Finalized labels](generation_baseline_v1_human_review.json) · [Summary JSON](generation_baseline_v1_summary.json) · [Frozen raw baseline](generation_baseline_v1.json)

| Dimension | Result | Eligible cases | N/A excluded |
| --- | ---: | ---: | ---: |
| Correctness | 3/17 (17.65%) | 17 | 2 |
| Groundedness | 5/19 (26.32%) | 19 | 0 |
| Mean completeness | 1.000 | 16 | 3 |
| Full-completeness rate | 16/16 (100.00%) | 16 | 3 |
| Refusal correctness | 3/3 (100.00%) | 3 | 16 |
| Citation correctness | 3/17 (17.65%) | 17 | 2 |
| Prompt compliance | 2/3 (66.67%) | 3 | 16 |

Each dimension excludes its own N/A labels. Binary metrics include cases with an integer label. Completeness covers answerable cases only; eligible IDs are recorded in the summary JSON.

Required-point completeness is reported separately. Full completeness does not override a human-labeled unsupported claim.

## Human-reported failures

| Dimension | Failed cases |
| --- | ---: |
| Correctness | 14 |
| Groundedness | 14 |
| Refusal correctness | 0 |
| Citation correctness | 14 |
| Prompt compliance | 1 |
| Incomplete answers | 0 |

Distinct cases failing at least one evaluated dimension: **15**. Counts across dimensions overlap.

| Qualitative category | Cases |
| --- | ---: |
| unsupported elaboration / over-generation | 14 |
| refusal output-format noncompliance | 1 |

Categories summarize reviewer-entered issues and labels. They do not come from a new inspection of generated answers.

| Case | Supplied reviewer issue / note |
| --- | --- |
| retrieval_001 | adds overshooting, erratic updates and tuning claims not supported by supplied context |
| retrieval_002 | adds majority/minority-class explanation and additional metric claims beyond supplied evidence |
| retrieval_004 | strengthens "reduce starvation" into eventual-execution/fairness guarantees not supplied by context |
| retrieval_006 | supplies precision formula and other claims not present in supplied notes |
| retrieval_007 | adds decomposition/data-integrity wording beyond supplied evidence |
| retrieval_008 | adds unsupported anomaly relationship |
| retrieval_009 | claims concurrency control is essential to maintain durability |
| retrieval_010 | overstates prevention/concurrency-control claims |
| retrieval_012 | adds outliers and unsupported explanatory/remedy claims |
| retrieval_013 | adds bias/robustness/overfitting claims beyond supplied context |
| retrieval_014 | adds unsupported claim relating 1NF to preventing anomalies |
| retrieval_015 | adds unsupported inconsistency and false-positive significance claims |
| retrieval_016 | adds function-call, local-variable and execution-flow explanations absent from notes |
| retrieval_017 | adds convoy effect, starvation mitigation and general performance claims absent from supplied context |
| retrieval_019 | correctly refuses the unsupported F1 formula, but continues after "I don't know.", violating exact refusal-output behavior |

## Recorded execution

Vector + BM25 + RRF, top 5 chunks; GPT-4o-mini, temperature 0, max_tokens 800. The production prompt was unchanged.

Generation latency over 19 cases: mean **2.396s**, median **2.362s**, range **0.601–3.916s**, total **45.517s**.

Generation tokens across 19 cases: **22,393 input + 3,354 output = 25,747 total**. Embedding tokens are excluded.

API/runtime failures: **0**. Latency and usage were copied from the frozen baseline; generation was not rerun.

Existing corpus inventory issue retained from the baseline:

- Corpus mismatch: chunk e3380555-fb30-454c-9a43-f8e3d66c05b9 present in whoosh, missing from chroma
