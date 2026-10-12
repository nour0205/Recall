# LLM judge calibration

An LLM judge grades Recall answers so evaluation no longer depends on manual review of every run. Before trusting it, I measured how often it agrees with my own labels on the 76 answers I reviewed by hand in Milestone 2 (4 prompts × 19 questions).

```sh
python -m evaluation.run_judge calibrate
python -m evaluation.run_judge end-to-end evaluation/results/end_to_end_v1_<timestamp>.json
```

## Setup

- **Judge:** `gpt-5.5-2026-04-23` (pinned snapshot), reasoning effort medium, strict structured output. Recall itself answers with `gpt-4o-mini`.
- **Same inputs and rubric as the human review.** The judge sees the question, the five numbered sources exactly as the answering model saw them, the answer, the expected behavior, the required points, the reference answer and the benchmark author's case notes. The rubric is read from [`generation_reference_v1.json`](benchmarks/generation_reference_v1.json), the same file the human review used. Human labels and reviewer notes are excluded by construction ([`judge.py`](judge.py), tested in `tests/test_judge.py`).
- **Claims before labels.** The judge first lists each factual claim with its supporting sources and citations, then judges each required point, then assigns the labels.
- **Prompt:** [`prompts/judge_v1.json`](prompts/judge_v1.json). One change was made before calibrating: the human labels use `N/A` for refusal correctness when an answerable question was simply answered, so the judge was given the same convention. No prompt changes were made after seeing calibration results.

## Agreement with human labels

[Raw results](results/judge_calibration_v1_20261012T081253Z.json): 76/76 answers judged, no invalid outputs. Kappa is Cohen's kappa, which corrects for agreement expected by chance. It is computed on the cases where the human label is 0 or 1, because `N/A` cases (pure refusals) are trivially easy to agree on and would inflate it.

| Dimension | Agreement | Kappa | Judge vs human | Verdict |
|---|---:|---:|---|---|
| Required points (completeness) | 141/144 | 0.86 | 2 lenient, 1 strict | **Trusted** |
| Correctness | 58/64 | 0.79 | 4 lenient, 2 strict | **Trusted, with spot checks** |
| Groundedness | 67/76 | 0.69 | 4 lenient, 5 strict | **Screen only; human review of failures and of known-hard cases** |
| Citation correctness | 51/64 | 0.55 | 4 lenient, 9 strict | **Not trusted yet** |
| Refusal correctness | 12/13 | 0.63 | 1 strict | Too few refusal cases to judge |

Completeness scores differ from the human scores by 0.02 on average (mean absolute error over the 64 answerable cases).

### What the disagreements show

- **Citations: conventions, not random noise.** The judge's 9 stricter citation verdicts come from three patterns, none of which the written rubric settles:
  - **Trailing citations (3 cases):** one citation at the end of a short paragraph left an earlier sentence "uncited". When I reviewed, I accepted a trailing citation covering a short paragraph.
  - **Each cited source checked separately (2 cases):** in `[S1][S2]`, the judge required each source to support the claim on its own; I accepted the cited set together.
  - **The case 008 definitions (3 cases):** see the next point.
- **Groundedness, strict side: wording copied from the notes but attached to the wrong concept.** On case 008 (under Strict v1, Balanced v2 and Strict v2), the answer reuses the notes' sentence "non-key attributes must depend on the whole primary key" as the *definition* of partial dependency. I labelled that grounded but incorrect; the judge labelled it ungrounded.
- **Groundedness, where the judge was arguably right:** on case 003 (Strict v2), the judge flagged that the answer drops the notes' qualifier "usually" ("communication between processes *usually* requires IPC"). I passed it. By the rubric's own rule on preserving qualifiers, the judge's reading is defensible.
- **Groundedness, lenient side: the failure mode that matters most.** The judge missed 4 unsupported elaborations I had flagged, for example "a more reliable estimate of generalization" on case 013 and calling `student_id` the primary key on case 014. Lenient errors hide exactly what Recall is designed to prevent, so a judge "grounded" verdict is not enough on its own.
- **Refusal:** the one disagreement is the baseline answer that said "I don't know." and then kept going with supported content. The rubric says a refusal followed by unsupported content fails; I judged the continuation supported and passed it. The judge failed it.

## Scoring the production `/ask` run

[Judge results](results/judge_end_to_end_v1_20261012T081515Z.json) for [end-to-end run 1](results/end_to_end_v1_20261012T071846Z.json). 15 of the 19 production answers are word-for-word identical to Strict v2 answers I reviewed, so those keep their human labels. The judge supplies labels only for the 4 new answers.

**Self-consistency check:** on the 15 identical answers, the judge agreed with my labels on every dimension for 13. The other 2 are the same disagreements it showed during calibration (008 groundedness/citation, 012 one required point).

| Production `/ask`, 19 questions | Result | Source |
|---|---:|---|
| Grounded answers | 19/19 | 15 human + 4 judge |
| Correct (answerable) | 15/16 | 15 human + 4 judge |
| Citation correctness (answerable) | 15/16 | 15 human + 4 judge |
| Required points covered | 14.5/16 | 15 human + 4 judge |
| Out-of-scope questions refused | 3/3 | human |

Compared with the isolated Milestone 2 Strict v2 result (grounded 18/19, completeness 14.5/16, citations 15/16), production matches it. The one change is case 013, where the new production answer was judged grounded and complete. **Case 013 needs human confirmation:** it is a case where the judge was lenient during calibration. The failure on 011 is the judge's stricter citation convention described above.

## Next

1. **Judge v2:** decide the conventions the disagreements exposed (trailing citations, a set of cited sources, source wording attached to the wrong concept, dropped qualifiers), write them into the rubric, and give them to the judge. To avoid tuning on the test set, revise using the disagreements from two prompt runs and report agreement only on the other two.
2. Human review of the production answer to 013.
3. Use the judge for the planner on/off comparison and the chunk de-duplication experiment.
