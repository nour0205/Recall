# Milestone 3 — End-to-end evaluation

Milestones 1 and 2 measured retrieval and the answer prompt in isolation, with retrieval frozen for generation. Milestone 3 measures the system users actually get: the production `/ask` endpoint, end to end. It also makes evaluation repeatable without hand-labelling every run, and uses that to test a component.

## What was built

| Piece | What it does | Details |
|---|---|---|
| Demo corpus | The 12 benchmark notes, recovered from the original indexes and versioned in [`demo_notes/`](../demo_notes/). Re-ingesting them reproduces the original 27 chunks exactly; a manifest maps every benchmark chunk ID to its note and position. | `python -m app.seed_demo` |
| End-to-end runner | Seeds a fresh temporary install, sends the 19 benchmark questions through the real `/ask`, and records answers, retrieved context, prompt fingerprints, latency and tokens. | [END_TO_END_EVALUATION.md](END_TO_END_EVALUATION.md) |
| LLM judge | GPT-5.5 (pinned) grades answers with the human-review rubric, seeing exactly what the human reviewer saw. Calibrated against the 76 human-labelled Milestone 2 answers. | [JUDGE_CALIBRATION.md](JUDGE_CALIBRATION.md) |
| Planner ablation | `/ask` with and without the LLM intent planner. | [PLANNER_ABLATION.md](PLANNER_ABLATION.md) |
| Retrieval rescoring | Vector-only, keyword-only and hybrid search scored on the evidence-group labels, from saved Milestone 1 rankings. | [rescoring](results/evidence_rescore_20261013T141146718706Z.md) |

## Results

**Production `/ask`, 19 questions:** grounded 17/19, correct 13/16, citation correctness 14/16, required points 14.25/16, refusals 3/3, no false refusals, required evidence retrieved for 16/16. Labels: human labels for the 15 answers identical to reviewed Milestone 2 answers, and the [adjudicated](results/end_to_end_v1_adjudications.json) rubric with written conventions for the 4 new ones. This matches the isolated Milestone 2 result once the same conventions apply to both.

**Judge agreement with human labels** (Cohen's kappa on 0/1 labels, judge v2): required points 0.82, correctness 0.75, groundedness 0.75, citations 0.61. Trusted for required points and correctness; used as a screen for groundedness and citations. Both judge versions miss the same 4 subtle unsupported claims, and v2's numbers are optimistic because its conventions were written after reading the disagreements.

**Planner:** the answering model received byte-identical prompts with and without the planner for all 19 questions, while the planner took about 40% of latency. It was removed; mean latency went from about 2.1 s to 1.2 s.

**Retrieval:** on the evidence labels, vector-only, keyword-only and hybrid search all put every required passage in the top 5 for all 16 answerable questions. They differ on single questions, so this benchmark cannot separate them. The Milestone 1 finding that vector-only search scored best came from the stricter exact-chunk labels.

**Run-to-run noise:** temperature 0 is not deterministic. Two runs with byte-identical prompts differ on 2 of 19 answers, and on one question one run was wrong and the other correct. Comparisons need several runs per configuration.

## Pilot of the v3 benchmark (draft, unreviewed)

48 new questions ([draft](drafts/benchmark_v3_review.md)) run twice through the planner-free `/ask`, and one run scored by judge v2. Exact refusals were labelled with the rubric's fixed refusal labels, which reproduce every human label for exact refusals in Milestone 2. [Run 1](results/end_to_end_benchmark_v3_draft_20261013T143406Z.json) · [run 2](results/end_to_end_benchmark_v3_draft_20261013T143512Z.json) · [judge](results/judge_end_to_end_judge_v2_20261013T145257Z.json)

| Category | Grounded | Correct | Citations | Required points |
|---|---:|---:|---:|---:|
| Paraphrase (10) | 10/10 | 10/10 | 10/10 | 8/10 |
| Exact term (8) | 8/8 | 8/8 | 8/8 | 8/8 |
| Multi-part (6) | 6/6 | 6/6 | 6/6 | 6/6 |
| Cross-note (6) | 4/6 | 4/6 | 3/6 | 5/6 |
| Qualifier traps (4) | 4/4 | 2/4 | 2/4 | 1/4 |
| Refusal cases (14) | 14/14 correctly refused, in both runs | | | |

- **Retrieval is still saturated:** the required evidence was retrieved for 34/34 answerable questions in both runs, including paraphrases and cross-note questions. With 27 chunks, the top 5 covers almost a fifth of the corpus; separating retrieval methods needs a larger corpus, not only harder questions.
- **Refusals are reliable:** all 10 near-miss traps (topic present, detail absent) and all 4 out-of-scope questions were refused in both runs.
- **New weaknesses the 19-question set could not show:** "always?" questions are falsely refused (v3_031 and v3_034, in both runs); combining two notes invites elaboration and dropped qualifiers (v3_020, v3_021); and some answers name a concept without its mechanism (v3_005, v3_008).
- **Run-to-run noise:** 41 of 48 answers were identical across the two runs; the behaviour counts above were identical.
- **Held-out check of the judge:** on 20 random answers labelled by the author, the judge matched all 32 required-point judgments, including all 4 failures (kappa 1.00). Groundedness and citations could not be tested this way: the author labelled all 20 grounded, so the sample held no failures; the only disagreement was the judge being stricter on one answer. [Details](JUDGE_CALIBRATION.md#held-out-check-on-new-answers-v3-pilot).

A live run of the planner-free `/ask` on the original 19 questions (two runs) confirmed one model call per question and prompts identical to the planner ablation's planner-off run. Latency varied from 1.3 s to 4.4 s between the two runs, entirely inside the OpenAI API call, so latency claims need several runs.

## Decisions

- **Removed the intent planner.** Structural evidence: it could not change the answer prompt.
- **Kept hybrid search; MiniLM stays experiment-only, for now.** Neither choice is supported or contradicted at this scale; both get re-tested on a larger corpus.
- **Adopted labelling conventions C1–C4** for citations, misread source wording and dropped qualifiers. The published Milestone 2 labels are unchanged.
- **Fixed index consistency** found along the way: ingestion is now all-or-nothing across the vector and keyword indexes, deletion removes a note from both, and notes without a course can be added again.

## Not yet done

1. **Review and freeze the v3 benchmark** (author review of the 48 draft questions; several were flagged for a decision).
2. **Held-out test of judge groundedness and citations:** done for required points; groundedness and citations need a labelled sample that contains failures.
3. **Fix the measured weaknesses** (false refusals on qualifier questions, elaboration when combining notes, short answers), measured on the frozen v3 set over several runs.

## Limits

19 questions over 12 short notes. Results describe behaviour on this set; no statistical-significance claims are made.
