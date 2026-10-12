# Planner ablation: `/ask` with and without the intent planner

Before answering, `/ask` calls `gpt-4o-mini` to classify the question's intent (`concept_explanation`, `source_recall`, `exam_preparation` or `unknown`) and to pick target documents from a registry. This experiment asks whether that call changes anything.

```sh
python -m evaluation.run_end_to_end                # planner on
python -m evaluation.run_end_to_end --no-planner   # planner skipped: route "unknown", no targets
```

Both runs use the end-to-end runner: a fresh install seeded from `demo_notes/`, the 19 benchmark questions, the real `/ask` endpoint. The runner records a SHA-256 fingerprint of every prompt sent to the model, so the two configurations can be compared on exactly what the answering model received, not only on its noisy output.

## Results

| | Planner on (run 1) | Planner on (run 2) | Planner off |
|---|---:|---:|---:|
| Answer prompts identical to planner-on run 2 | | | **19/19** |
| Retrieved context identical to planner-on run 2 | | | **19/19** |
| Answers identical to planner-on run 2 | 17/19 | | 17/19 |
| Planner model calls | 19 | 19 | 0 |
| Mean latency | 2.17 s | 2.06 s | **1.21 s** |
| p90 latency | 3.25 s | 2.50 s | **1.62 s** |
| Chat tokens | 32,134 | 32,103 | **22,945** |
| Refusals / false refusals / evidence retrieved | 3/3, 0/16, 16/16 | 3/3, 0/16, 16/16 | 3/3, 0/16, 16/16 |
| Judge v2: grounded / required points | 18/19, 14.75/16 | | 18/19, 15.25/16 |

Raw results: [on, run 1](results/end_to_end_v1_20261012T071846Z.json) · [on, run 2](results/end_to_end_v1_20261012T113636Z.json) · [off](results/end_to_end_v1_no_planner_20261012T113759Z.json) · judge v2 [on](results/judge_end_to_end_judge_v2_20261012T084520Z.json) / [off](results/judge_end_to_end_judge_v2_20261012T113901Z.json)

## Findings

- **The planner had no effect on any answer.** With and without it, the answering model received byte-identical prompts for all 19 questions, built from identical retrieved context. The planner never selected target documents (its registry lists PostgreSQL, SQL Server and MongoDB notes that are not in the corpus), and the answer prompt does not use the route. The route only changes the rule-based study tip.
- **It costs about 40% of latency and 29% of chat tokens.** Removing it cut mean latency from about 2.1 s to 1.2 s and p90 from 2.5–3.3 s to 1.6 s.
- **Its classification is unstable.** On the same questions it returned `concept_explanation` for 3 questions in run 1 and 4 in run 2; everything else was `unknown`.
- **Run-to-run noise is real, even at temperature 0.** Two planner-on runs differ on 2 of 19 answers, exactly as many as planner on vs off. The clearest case is 008: from byte-identical prompts, one run defined both dependencies incorrectly and the other correctly. The judge's slightly higher completeness for the planner-off run is this noise, not an effect of removing the planner.

## Decision

Remove the planner from the production `/ask` path. If intent-specific behavior is wanted later (for example, a study-plan format for exam questions), it should be added together with a prompt that actually uses the intent, and evaluated against this baseline.

Future comparisons should use several runs per configuration: on 19 questions, a single run can move a score by about one case from chance alone.
