# RAGAS compared with the human labels and the calibrated judge

[RAGAS](https://docs.ragas.io) is the standard off-the-shelf library for scoring RAG answers. This experiment asks whether its metrics could replace or support Recall's custom judge, measured the same way the judge was: against the 76 human-labelled Milestone 2 answers.

## Setup

- RAGAS 0.4.3 in its own pinned environment ([`requirements-ragas.txt`](requirements-ragas.txt)); grader gpt-4o-mini at temperature 0, embeddings `text-embedding-3-small`.
- Metrics: faithfulness (claims supported by the retrieved context), factual correctness (claims compared with the reference answer, F1), context recall (reference claims found in the context), answer relevancy (questions regenerated from the answer, compared with the real question).
- Exact `I don't know.` answers are skipped: they make no claims, and refusal behaviour is already labelled deterministically. That leaves 64 of the 76 calibration answers and 32 of the 48 v3 answers.
- Code: [`run_ragas.py`](run_ragas.py), [`ragas_data.py`](ragas_data.py) (input building and calibration maths, unit-tested offline).

```sh
python -m venv .venv-ragas
.venv-ragas/Scripts/python -m pip install -r evaluation/requirements-ragas.txt
.venv-ragas/Scripts/python -m evaluation.run_ragas calibrate
.venv-ragas/Scripts/python -m evaluation.run_ragas run evaluation/results/<end-to-end run>.json
```

## Calibration against the human labels

[Result file](results/ragas_calibration_20261016T130348Z.json). The judge's agreement is recomputed on the same 64 answers from the [judge v2 calibration](results/judge_calibration_judge_v2_20261012T084333Z.json), so the comparison is like for like.

| Human label | RAGAS metric | AUC | Best threshold | Agreement (kappa) | Missed failures | False alarms | Judge v2 on the same 64 |
|---|---|---:|---:|---|---:|---:|---|
| Groundedness (19 failures) | faithfulness | 0.85 | ≥ 0.9 | 51/64 (0.58) | 1 | 12 | 57/64 (0.73): 4 missed, 3 false alarms |
| Correctness (22 failures) | factual correctness | 0.77 | ≥ 0.8 | 48/64 (0.48) | 5 | 11 | 57/64 (0.75): 4 missed, 3 false alarms |

AUC is the probability that a randomly chosen answer the author passed scores higher than one the author failed (0.5 is chance). Kappa and the missed/false-alarm counts come from turning the score into pass/fail at a threshold; all five tested thresholds (1.0, 0.9, 0.8, 0.7, 0.5) are in the result file. The best threshold was chosen on these same 64 answers, so the RAGAS rows are slightly optimistic.

- **Faithfulness ranks answers usefully but has no good cut-off.** Answers the author labelled grounded score anywhere from 0.5 to 1.0. A strict threshold catches almost every failure but rejects 12 of 45 good answers; a looser one lets failures through.
- **Factual correctness is weaker.** It penalises correct answers that are shorter than the reference or phrased differently; two answers the author labelled correct scored 0.0.
- **Context recall** averaged 0.98: retrieval is saturated on this benchmark, as the retrieval rescoring already showed.
- **Answer relevancy** averaged 0.69 and punishes the deliberately short Strict v2 answers. RAGAS asks the grader for 3 regenerated questions per answer, but gpt-4o-mini returned 1, so each score rests on one sample.

## Production v3 run

[Result file](results/ragas_end_to_end_benchmark_v3_draft_20261013T143406Z_20261016T132015Z.json), scoring the [first v3 pilot run](results/end_to_end_benchmark_v3_draft_20261013T143406Z.json), compared with [judge v2 on the same run](results/judge_end_to_end_judge_v2_20261013T145257Z.json).

Means over the 32 non-refusal answers: faithfulness 0.93, factual correctness 0.76, context recall 0.94, answer relevancy 0.74.

- **Faithfulness below 0.9 on 5 answers.** It agrees with the judge on v3_021 (elaboration when combining notes) but scores v3_020 at 1.0, although that answer adds performance claims and drops the sources' qualifiers (convention C4). It also flags v3_017, whose definition of recall matches the source sentence.
- **Factual correctness below 0.8 on 12 of the 30 answers the judge passed for correctness.** Three correct answers score 0.0 because the reference is a terse phrase ("Once.", "Multiversion concurrency control.", the four confusion-matrix counts). Its low scores do overlap with the answers that miss a required point (v3_005, v3_008, v3_033).
- **Context recall 0.0 on v3_016 and v3_033,** although the quoted evidence was retrieved for every answerable v3 question.

## Conclusion

On every comparison, the calibrated judge agrees with the human labels more than the RAGAS metrics do, and RAGAS misses the convention-specific failures (dropped qualifiers, unsupported elaboration across notes) that matter most for Recall's strict answers. RAGAS faithfulness is kept as a cheap second opinion that ranks answers by groundedness; the custom judge, with human review of its "grounded" verdicts, stays the primary scorer.

Cost: about 406k input and 92k output grader tokens for the calibration and 192k / 29k for the v3 run, all with gpt-4o-mini.

## Limits

64 and 32 answers, one RAGAS run each, one grader model. Thresholds were chosen on the calibration data. No statistical-significance claims are made.
