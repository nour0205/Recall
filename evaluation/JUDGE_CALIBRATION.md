# LLM judge calibration

An LLM judge grades Recall answers so evaluation no longer depends on manual review of every run. Before trusting it, I measured how often it agrees with my own labels on the 76 answers I reviewed by hand in Milestone 2 (4 prompts × 19 questions).

```sh
python -m evaluation.run_judge calibrate                       # judge_v2 by default
python -m evaluation.run_judge --prompt evaluation/prompts/judge_v1.json calibrate
python -m evaluation.run_judge end-to-end evaluation/results/end_to_end_v1_<timestamp>.json
```

## Setup

- **Judge:** `gpt-5.5-2026-04-23` (pinned snapshot), reasoning effort medium, strict structured output. Recall itself answers with `gpt-4o-mini`.
- **Same inputs and rubric as the human review.** The judge sees the question, the five numbered sources exactly as the answering model saw them, the answer, the expected behavior, the required points, the reference answer and the benchmark author's case notes. The rubric is read from [`generation_reference_v1.json`](benchmarks/generation_reference_v1.json), the same file the human review used. Human labels and reviewer notes are excluded by construction ([`judge.py`](judge.py), tested in `tests/test_judge.py`).
- **Claims before labels.** The judge first lists each factual claim with its supporting sources and citations, then judges each required point, then assigns the labels.
- **Two prompt versions.** [`judge_v1`](prompts/judge_v1.json) uses the rubric as written. One change was made to it before calibrating: the human labels use `N/A` for refusal correctness when an answerable question was simply answered, so the judge got the same convention. [`judge_v2`](prompts/judge_v2.json) adds four labelling conventions written after reading v1's disagreements (below).

## Agreement with human labels

Kappa is Cohen's kappa, which corrects for agreement expected by chance. It is computed on the cases where the human label is 0 or 1, because `N/A` cases (pure refusals) are trivially easy to agree on and would inflate it. All 76 answers were judged without invalid outputs in both runs.

| Dimension | v1 agreement | v1 kappa | v2 agreement | v2 kappa | Verdict |
|---|---:|---:|---:|---:|---|
| Required points (completeness) | 141/144 | 0.86 | 140/144 | 0.82 | **Trusted** |
| Correctness | 58/64 | 0.79 | 57/64 | 0.75 | **Trusted, with spot checks** |
| Groundedness | 67/76 | 0.69 | 69/76 | 0.75 | **Screen only** (see blind spot) |
| Citation correctness | 51/64 | 0.55 | 53/64 | 0.61 | **Not trusted yet** |
| Refusal correctness | 12/13 | 0.63 | 12/13 | 0.63 | Too few refusal cases to judge |

Raw results: [v1](results/judge_calibration_v1_20261012T081253Z.json), [v2](results/judge_calibration_judge_v2_20261012T084333Z.json). Completeness scores differ from the human scores by 0.02 on average.

**v2's numbers are optimistic.** Its conventions were written after reading the disagreements on these same 76 answers, so this is not a held-out test. A clean test needs new human-labelled answers; the larger benchmark will provide them.

### Labelling conventions (judge v2)

v1's disagreements were not random: most came from cases the rubric never settled, which I had resolved one way during review without writing it down. v2 writes them down:

| | Convention | Origin |
|---|---|---|
| C1 | A citation at the end of a short paragraph (≤ 3 sentences) covers that paragraph's claims if the cited sources support them. | How the human review was done |
| C2 | `[S1][S2]` passes when the cited sources *together* support the claim, provided each supports part of it. | How the human review was done |
| C3 | Wording reused from the sources but attached to the wrong concept is **grounded but incorrect**, and the affected point fails. | How the human review was done (case 008) |
| C4 | Dropping or weakening a source qualifier (*may, usually, often…*) so the claim becomes stronger fails groundedness and correctness. | Recall's own prompt, rule 10 |

C4 means some original human labels were too lenient. On question 003, the Baseline, Strict v1 and Strict v2 answers turn "communication between processes *usually* requires IPC" into "requires IPC" (Balanced v2 keeps "usually"), and I passed all of them. The Milestone 2 labels are frozen and stay as published; under C4, Strict v2 would score 17/19 grounded rather than 18/19. The other 75 answers were not re-reviewed for C4.

### What the disagreements show

- **A stable blind spot: subtle unsupported elaborations.** Both judge versions missed the **same 4** unsupported claims I had flagged, for example "a more reliable estimate of generalization" (013, Strict v2) and calling `student_id` the primary key (014, Balanced v2). These lenient errors hide exactly what Recall is designed to prevent, so a judge "grounded" verdict is not enough on its own.
- **Inconsistency on borderline cases.** On the near-identical 003 answers, v1 applied the "usually" reading to Strict v2 only, while v2 applied it to Baseline and Strict v1 but not Strict v2. Single-run verdicts on borderline cases vary.
- **What the conventions fixed.** v2 labels the 008 definitions grounded-but-incorrect like the human review (C3), and its stricter citation verdicts fell from 9 to 7 (C1, C2). Those remaining are mostly 008 definitions and 003 qualifiers, where the judge follows the conventions and the original labels do not.
- **Refusal:** the one disagreement is the baseline answer that said "I don't know." and then kept going. The rubric says a refusal followed by unsupported content fails; I judged the continuation supported and passed it.

## Scoring the production `/ask` run

Scores for [end-to-end run 1](results/end_to_end_v1_20261012T071846Z.json). 15 of the 19 production answers are word-for-word identical to Strict v2 answers I reviewed, so they keep their human labels. The 4 new answers were [adjudicated](results/end_to_end_v1_adjudications.json) with the rubric and conventions C1–C4. Judge v2 agreed on 3 of them, and missed the added explanation in 013, its known blind spot.

**Self-consistency check:** on the 15 identical answers, judge v2 matched the human labels except for the cases it also disagreed on in calibration (008 citations, 012 one required point).

| Production `/ask`, 19 questions | Result |
|---|---:|
| Grounded answers | 17/19 |
| Correct (answerable) | 13/16 |
| Citation correctness (answerable) | 14/16 |
| Required points covered | 14.25/16 |
| Out-of-scope questions refused | 3/3 |

The new failures are 003 (dropped "usually", C4) and 013 (an added explanation about single splits). Under the same conventions, the isolated Milestone 2 Strict v2 answer to 003 fails as well, so production is in line with Milestone 2, not worse. The Milestone 2 headline (18/19 grounded) used labels made before C4 existed.

## Next

1. Use the judge as a **screen**: trust its required-point and correctness verdicts, but review by hand every answer it fails on groundedness or citations, plus a sample of those it passes.
2. Grow the benchmark with new human-labelled answers. They give a held-out test for judge v2 and more refusal cases.
3. Use this setup for the planner on/off comparison and the chunk de-duplication experiment.
