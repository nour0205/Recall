# Controlled Grounded-Prompt Ablation

Controlled 19-case benchmark (16 answerable, 3 refusal cases). Conclusions are limited to this evaluation set; no statistical significance is claimed.

Finalized human labels only. Each dimension has its own eligible denominator; no weighted overall score.

| Dimension | Baseline | Strict v1 | Balanced v2 |
| --- | ---: | ---: | ---: |
| correctness | 3/17 (17.65%) | 14/15 (93.33%) | 11/16 (68.75%) |
| groundedness | 5/19 (26.32%) | 19/19 (100.00%) | 15/19 (78.95%) |
| mean_completeness | 16/16 (100.00%) | 13.5/16 (84.38%) | 15.5/16 (96.88%) |
| full_completeness_rate | 16/16 (100.00%) | 12/16 (75.00%) | 15/16 (93.75%) |
| refusal_correctness | 3/3 (100.00%) | 3/4 (75.00%) | 3/3 (100.00%) |
| citation_correctness | 3/17 (17.65%) | 15/15 (100.00%) | 12/16 (75.00%) |
| prompt_compliance | 2/3 (66.67%) | 3/4 (75.00%) | 3/3 (100.00%) |

| Failures / efficiency | Baseline | Strict v1 | Balanced v2 |
| --- | ---: | ---: | ---: |
| Unsupported elaboration (cases) | 14 | 0 | 4 |
| Distinct cases failing a dimension | 15 | 4 | 5 |
| Latency mean (seconds) | 2.396 | 1.479 | 1.63 |
| Latency median (seconds) | 2.362 | 1.151 | 1.41 |
| Latency total (seconds) | 45.517 | 28.104 | 30.961 |
| prompt_tokens | 22393 | 19942 | 22849 |
| completion_tokens | 3354 | 525 | 829 |
| total_tokens | 25747 | 20467 | 23678 |
| average_answer_words | 135.16 | 20.79 | 34 |
| average_answer_characters | 926.42 | 141.68 | 224.53 |

- Baseline: high completeness, poor groundedness/citation correctness, 14 unsupported-elaboration failures.
- Strict v1: strongest grounding/citation quality, lower completeness, one false refusal and under-answering behavior.
- Balanced v2: recovers most completeness and fixes strict omissions and false refusal, but reintroduces some unsupported elaboration.

Strict refusal correctness is 3/4 across all human-labeled refusal decisions, including the failed refusal on answerable case 004. Expected refusal cases alone pass 3/3. Strict prompt compliance similarly includes case 004 (3/4).

## Reviewed case transitions

Cells show correctness / groundedness / completeness / citation correctness / refusal correctness / prompt compliance, followed by failed point IDs and supplied issues or notes. N/A remains excluded. Exact point judgments and evidence-group coverage are recorded in the JSON.

| Case | Baseline | Strict v1 | Balanced v2 |
| --- | --- | --- | --- |
| retrieval_004 | 0 / 0 / 1.0 / 0 / N/A / N/A — strengthens "reduce starvation" into eventual-execution/fairness guarantees not supplied by context | N/A / 1 / 0.0 / N/A / 0 / 0 — Failed points: priority, starvation; incorrect refusal despite sufficient supplied evidence | 1 / 1 / 1.0 / 1 / N/A / N/A — false refusal seen in strict_v1 is fixed |
| retrieval_007 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds decomposition/data-integrity wording beyond supplied evidence | 1 / 1 / 1.0 / 1 / N/A / N/A | 0 / 0 / 1.0 / 0 / N/A / N/A — calls student_id the primary key, which is not explicitly supported by the supplied context |
| retrieval_008 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds unsupported anomaly relationship | 0 / 1 / 0.5 / 1 / N/A / N/A — Failed points: partial_definition, transitive_definition; response states the normalized condition rather than correctly expressing both dependency definitions | 0 / 1 / 0.5 / 1 / N/A / N/A — Failed points: partial_definition, transitive_definition; response states the normalized condition rather than correctly expressing both dependency definitions |
| retrieval_010 | 0 / 0 / 1.0 / 0 / N/A / N/A — overstates prevention/concurrency-control claims | 1 / 1 / 0.5 / 1 / N/A / N/A — Failed points: mechanism; correctly names non-repeatable read but omits the mechanism | 1 / 1 / 1.0 / 1 / N/A / N/A — strict_v1 omission fixed; both name and mechanism present |
| retrieval_012 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds outliers and unsupported explanatory/remedy claims | 1 / 1 / 0.5 / 1 / N/A / N/A — Failed points: pattern; correctly names overfitting but omits the strong-training / poor-unseen-data pattern | 1 / 1 / 1.0 / 1 / N/A / N/A — strict_v1 omission fixed; both name and pattern present |
| retrieval_013 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds bias/robustness/overfitting claims beyond supplied context | 1 / 1 / 1.0 / 1 / N/A / N/A | 0 / 0 / 1.0 / 0 / N/A / N/A — adds unsupported claim about mitigating bias from a single random split |
| retrieval_014 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds unsupported claim relating 1NF to preventing anomalies | 1 / 1 / 1.0 / 1 / N/A / N/A | 0 / 0 / 1.0 / 0 / N/A / N/A — calls student_id the primary key without explicit support |
| retrieval_017 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds convoy effect, starvation mitigation and general performance claims absent from supplied context | 1 / 1 / 1.0 / 1 / N/A / N/A | 0 / 0 / 1.0 / 0 / N/A / N/A — adds unsupported explanation about process length, shorter-task waiting, and timely attention |
| retrieval_019 | 1 / 1 / N/A / 1 / 1 / 0 — correctly refuses the unsupported F1 formula, but continues after "I don't know.", violating exact refusal-output behavior | N/A / 1 / N/A / N/A / 1 / 1 | N/A / 1 / N/A / N/A / 1 / 1 |

[Comparison JSON](generation_prompt_ablation_comparison_v1.json)
