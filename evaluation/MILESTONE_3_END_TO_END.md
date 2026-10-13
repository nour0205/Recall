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

## Decisions

- **Removed the intent planner.** Structural evidence: it could not change the answer prompt.
- **Kept hybrid search; MiniLM stays experiment-only, for now.** Neither choice is supported or contradicted at this scale; both get re-tested on a larger corpus.
- **Adopted labelling conventions C1–C4** for citations, misread source wording and dropped qualifiers. The published Milestone 2 labels are unchanged.
- **Fixed index consistency** found along the way: ingestion is now all-or-nothing across the vector and keyword indexes, deletion removes a note from both, and notes without a course can be added again.

## Not yet done

1. **A larger benchmark** with harder retrieval questions (paraphrases with no shared words, exact technical terms) and more refusal traps than the current 3.
2. **A held-out test of judge v2** on newly human-labelled answers.
3. **Several end-to-end runs per configuration**, including a live run of the planner-free `/ask`.

## Limits

19 questions over 12 short notes. Results describe behaviour on this set; no statistical-significance claims are made.
