# Controlled Grounded-Prompt Ablation

Controlled 19-case benchmark (16 answerable, 3 refusal cases). Conclusions are limited to this evaluation set; no statistical significance is claimed.

Finalized human labels only. Each dimension has its own eligible denominator; no weighted overall score.

| Dimension | Baseline | Strict v1 | Balanced v2 | Strict v2 |
| --- | ---: | ---: | ---: | ---: |
| correctness | 3/17 (17.65%) | 14/15 (93.33%) | 11/16 (68.75%) | 14/16 (87.50%) |
| groundedness | 5/19 (26.32%) | 19/19 (100.00%) | 15/19 (78.95%) | 18/19 (94.74%) |
| mean_completeness | 16/16 (100.00%) | 13.5/16 (84.38%) | 15.5/16 (96.88%) | 14.5/16 (90.62%) |
| full_completeness_rate | 16/16 (100.00%) | 12/16 (75.00%) | 15/16 (93.75%) | 13/16 (81.25%) |
| refusal_correctness | 3/3 (100.00%) | 3/4 (75.00%) | 3/3 (100.00%) | 3/3 (100.00%) |
| citation_correctness | 3/17 (17.65%) | 15/15 (100.00%) | 12/16 (75.00%) | 15/16 (93.75%) |
| prompt_compliance | 2/3 (66.67%) | 3/4 (75.00%) | 3/3 (100.00%) | 3/3 (100.00%) |

| Failures / efficiency | Baseline | Strict v1 | Balanced v2 | Strict v2 |
| --- | ---: | ---: | ---: | ---: |
| Unsupported elaboration (cases / eligible) | 14/19 | 0/19 | 4/19 | 1/19 |
| Distinct cases failing a dimension | 15 | 4 | 5 | 4 |
| Latency mean (seconds) | 2.396 | 1.479 | 1.63 | 1.132 |
| Latency median (seconds) | 2.362 | 1.151 | 1.41 | 1.007 |
| Latency total (seconds) | 45.517 | 28.104 | 30.961 | 21.501 |
| prompt_tokens | 22393 | 19942 | 22849 | 22393 |
| completion_tokens | 3354 | 525 | 829 | 569 |
| total_tokens | 25747 | 20467 | 23678 | 22962 |
| average_answer_words | 135.16 | 20.79 | 34 | 22.37 |
| average_answer_characters | 926.42 | 141.68 | 224.53 | 152.32 |

- Baseline: maximum completeness, poor groundedness/citation correctness, 14 unsupported-elaboration failures.
- Strict v1: strongest grounding and zero unsupported elaboration, but too conservative on some supported questions; one false refusal and under-answering.
- Balanced v2: recovers completeness and fixes the false refusal, but reintroduces unsupported content.
- Strict v2: targeted completeness refinement of Strict v1; fixes the false refusal and improves completeness, but still has one unsupported-elaboration case. Cases 008, 010, and 012 remain incomplete; case 013 contains unsupported elaboration. This demonstrates the measured completeness/grounding trade-off, not a universally best prompt.

Strict refusal correctness is 3/4 across all human-labeled refusal decisions, including the failed refusal on answerable case 004. Expected refusal cases alone pass 3/3. Strict prompt compliance similarly includes case 004 (3/4).

## Reviewed case transitions

Cells show correctness / groundedness / completeness / citation correctness / refusal correctness / prompt compliance, followed by failed point IDs and supplied issues or notes. N/A remains excluded. Exact point judgments and evidence-group coverage are recorded in the JSON.

| Case | Baseline | Strict v1 | Balanced v2 | Strict v2 |
| --- | --- | --- | --- | --- |
| retrieval_004 | 0 / 0 / 1.0 / 0 / N/A / N/A — strengthens "reduce starvation" into eventual-execution/fairness guarantees not supplied by context | N/A / 1 / 0.0 / N/A / 0 / 0 — Failed points: priority, starvation; incorrect refusal despite sufficient supplied evidence | 1 / 1 / 1.0 / 1 / N/A / N/A — false refusal seen in strict_v1 is fixed | 1 / 1 / 1.0 / 1 / N/A / N/A — Strict v1 false refusal fixed |
| retrieval_007 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds decomposition/data-integrity wording beyond supplied evidence | 1 / 1 / 1.0 / 1 / N/A / N/A | 0 / 0 / 1.0 / 0 / N/A / N/A — calls student_id the primary key, which is not explicitly supported by the supplied context | 1 / 1 / 1.0 / 1 / N/A / N/A |
| retrieval_008 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds unsupported anomaly relationship | 0 / 1 / 0.5 / 1 / N/A / N/A — Failed points: partial_definition, transitive_definition; response states the normalized condition rather than correctly expressing both dependency definitions | 0 / 1 / 0.5 / 1 / N/A / N/A — Failed points: partial_definition, transitive_definition; response states the normalized condition rather than correctly expressing both dependency definitions | 0 / 1 / 0.5 / 1 / N/A / N/A — Failed points: partial_definition, transitive_definition; still expresses normalized conditions rather than both dependency definitions |
| retrieval_010 | 0 / 0 / 1.0 / 0 / N/A / N/A — overstates prevention/concurrency-control claims | 1 / 1 / 0.5 / 1 / N/A / N/A — Failed points: mechanism; correctly names non-repeatable read but omits the mechanism | 1 / 1 / 1.0 / 1 / N/A / N/A — strict_v1 omission fixed; both name and mechanism present | 1 / 1 / 0.5 / 1 / N/A / N/A — Failed points: mechanism; names non-repeatable read but omits mechanism |
| retrieval_012 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds outliers and unsupported explanatory/remedy claims | 1 / 1 / 0.5 / 1 / N/A / N/A — Failed points: pattern; correctly names overfitting but omits the strong-training / poor-unseen-data pattern | 1 / 1 / 1.0 / 1 / N/A / N/A — strict_v1 omission fixed; both name and pattern present | 1 / 1 / 0.5 / 1 / N/A / N/A — Failed points: pattern; names overfitting but omits training-vs-unseen performance pattern |
| retrieval_013 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds bias/robustness/overfitting claims beyond supplied context | 1 / 1 / 1.0 / 1 / N/A / N/A | 0 / 0 / 1.0 / 0 / N/A / N/A — adds unsupported claim about mitigating bias from a single random split | 0 / 0 / 1.0 / 0 / N/A / N/A — response adds the unsupported explanation that evaluating across multiple splits provides a more reliable estimate of generalization in the exact claim form used |
| retrieval_014 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds unsupported claim relating 1NF to preventing anomalies | 1 / 1 / 1.0 / 1 / N/A / N/A | 0 / 0 / 1.0 / 0 / N/A / N/A — calls student_id the primary key without explicit support | 1 / 1 / 1.0 / 1 / N/A / N/A |
| retrieval_017 | 0 / 0 / 1.0 / 0 / N/A / N/A — adds convoy effect, starvation mitigation and general performance claims absent from supplied context | 1 / 1 / 1.0 / 1 / N/A / N/A | 0 / 0 / 1.0 / 0 / N/A / N/A — adds unsupported explanation about process length, shorter-task waiting, and timely attention | 1 / 1 / 1.0 / 1 / N/A / N/A |
| retrieval_019 | 1 / 1 / N/A / 1 / 1 / 0 — correctly refuses the unsupported F1 formula, but continues after "I don't know.", violating exact refusal-output behavior | N/A / 1 / N/A / N/A / 1 / 1 | N/A / 1 / N/A / N/A / 1 / 1 | N/A / 1 / N/A / N/A / 1 / 1 |

[Comparison JSON](generation_prompt_ablation_comparison_final.json)
