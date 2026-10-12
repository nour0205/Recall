# End-to-end evaluation of `/ask`

Milestones 1 and 2 evaluated retrieval and the prompt in isolation, with retrieval frozen for generation. This evaluation sends the 19 benchmark questions through the production `/ask` endpoint instead: live planner, live hybrid retrieval, the production Strict v2 prompt, production settings and fallbacks.

```sh
python -m evaluation.run_end_to_end
```

The runner seeds a fresh, temporary install from [`demo_notes/`](../demo_notes/) and checks that it reproduces the benchmark corpus exactly (27 chunks) before asking anything. Your own library is never touched. Each run writes a new timestamped file to `results/` and never overwrites one. Thin wrappers record the planner's output, the retrieved context and the token usage of every model call without changing behaviour.

**Answer quality is not scored here.** Rows record only facts that need no judgement: refusal behaviour, cited `[S#]` labels, and whether the retrieved context contained each required point's evidence (benchmark evidence groups, mapped to the fresh install by note and position). Correctness, groundedness and completeness will be scored by an LLM judge calibrated against the Milestone 2 human labels.

## Run 1 — 2026-10-12

[Raw results](results/end_to_end_v1_20261012T071846Z.json)

| Measure | Result |
|---|---:|
| Requests completed | 19/19 |
| Out-of-scope questions refused | 3/3 |
| Answerable questions falsely refused | 0/16 |
| Answerable questions with all required evidence retrieved | 16/16 |
| Answers containing citations | 16/16 |
| Answers citing a label that doesn't exist | 0 |
| Fallback path used | 0 |
| Latency, mean / median / max | 2.17 s / 1.97 s / 3.45 s |

### How production compares with the isolated benchmark

- **Retrieval:** 16 of 19 questions retrieved the same five passages in the same order as the frozen Milestone 2 context.
- **Answers:** 15 of 19 answers are word-for-word identical to the human-reviewed Strict v2 answers, so those human labels apply to production unchanged.
- **The other 4** (003, 011, 013, 016) state the same facts in different words, or format citations as `[S1], [S2]`. Three of them had identical retrieved context, so temperature 0 does not make the model fully deterministic. Run-to-run comparisons must allow for this noise. These 4 answers have no human label yet.

### The planner

| | Result |
|---|---:|
| Questions classified `unknown` | 16/19 |
| Questions classified `concept_explanation` | 3/19 |
| Questions where it narrowed the search | 0/19 |
| Share of chat tokens | 28% (9,130 of 32,134) |
| Mean latency of its call | 0.86 s of 2.17 s per request |

Every route uses the same prompt, so the planner's output did not change any answer in this run, while it accounted for roughly 40% of request latency. The [planner ablation](PLANNER_ABLATION.md) confirms it: with and without the planner, the answering model received byte-identical prompts for all 19 questions, while removing it cut mean latency from about 2.1 s to 1.2 s.

### Quality scores

Scored in [JUDGE_CALIBRATION.md](JUDGE_CALIBRATION.md#scoring-the-production-ask-run). The 15 answers identical to human-reviewed Strict v2 answers keep their human labels; the 4 new ones were [adjudicated](results/end_to_end_v1_adjudications.json) with the rubric and conventions C1-C4, with the calibrated judge as a second opinion. Production: grounded 17/19, correct 13/16, citation correctness 14/16, required points 14.25/16, refusals 3/3. The two new failures are a dropped "usually" (003), which the Milestone 2 answer also has under the same convention, and an added explanation (013).

### Limits

19 questions over 12 short notes, one run. These numbers describe behaviour on this set, not general performance. The judge and a larger benchmark are the next steps.
