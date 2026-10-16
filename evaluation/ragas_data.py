"""RAGAS inputs and calibration maths. Pure functions; RAGAS itself is not imported here.

RAGAS scores answers with continuous metrics (0 to 1). To know whether they can
be trusted for Recall, they are compared with the Milestone 2 human labels the
same way the LLM judge was: how well a score separates the answers a human
labelled 0 from those labelled 1 (AUC), and how often a score threshold agrees
with the human label (agreement, Cohen's kappa).
"""
import json
from pathlib import Path

from evaluation.generation_benchmark import REFERENCE_PATH
from evaluation.judge_agreement import cohens_kappa

REFUSAL = "I don't know."


def _row(question_id, question, contexts, answer, reference, **extra):
    return {"question_id": question_id, "user_input": question, "retrieved_contexts": contexts,
            "response": answer, "reference": reference, **extra}


def rows_from_run(run_path: Path) -> tuple[list[dict], list[str]]:
    """RAGAS rows for a saved end-to-end run; exact refusals are skipped (no claims to score)."""
    run = json.loads(Path(run_path).read_text(encoding="utf-8"))
    benchmark = (run.get("provenance") or {}).get("benchmark") or ""
    source = Path(benchmark) if Path(benchmark).name.startswith("benchmark_v3") else REFERENCE_PATH
    references = {c["question_id"]: c["reference_answer"] for c in json.loads(source.read_text(encoding="utf-8"))["cases"]}
    rows, skipped = [], []
    for q in run["queries"]:
        if (q["answer"] or "").strip() == REFUSAL:
            skipped.append(q["question_id"])
            continue
        contexts = [c["text"] for c in q["retrieved_context"] or [] if c["text"].strip()]
        rows.append(_row(q["question_id"], q["question"], contexts, q["answer"], references[q["question_id"]],
                         expected_behavior=q["expected_behavior"]))
    return rows, skipped


def rows_from_calibration(cases) -> tuple[list[dict], list[str]]:
    """RAGAS rows for the human-labelled Milestone 2 answers (evaluation.run_judge.calibration_cases())."""
    rows, skipped = [], []
    for c in cases:
        key = f"{c['run']}/{c['question_id']}"
        if (c["answer"] or "").strip() == REFUSAL:
            skipped.append(key)
            continue
        rows.append(_row(key, c["question"], [s["text"] for s in c["sources"]], c["answer"], c["reference_answer"],
                         expected_behavior=c["expected_behavior"], human=c["human"]))
    return rows, skipped


def auc(scores, labels) -> float | None:
    """Probability that a randomly chosen label-1 answer scores higher than a label-0 one (ties count half)."""
    positives = [s for s, y in zip(scores, labels) if y == 1]
    negatives = [s for s, y in zip(scores, labels) if y == 0]
    if not positives or not negatives:
        return None
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def threshold_agreement(scores, labels, threshold) -> dict:
    predicted = [1 if s >= threshold else 0 for s in scores]
    pairs = list(zip(labels, predicted))
    agree = sum(h == p for h, p in pairs)
    return {"threshold": threshold, "agreement": f"{agree}/{len(pairs)}",
            "agreement_rate": agree / len(pairs) if pairs else None, "kappa": cohens_kappa(pairs),
            "missed_failures": sum(h == 0 and p == 1 for h, p in pairs),
            "false_alarms": sum(h == 1 and p == 0 for h, p in pairs)}


def calibrate(rows, metric: str, human_dimension: str, thresholds=(1.0, 0.9, 0.8, 0.7, 0.5)) -> dict:
    """Compare one RAGAS metric with one human label; rows without a 0/1 label or a score are left out."""
    usable = [(r["scores"][metric], r["human"][human_dimension]) for r in rows
              if r["human"][human_dimension] in (0, 1) and r["scores"].get(metric) is not None]
    scores, labels = [s for s, _ in usable], [y for _, y in usable]
    return {
        "metric": metric, "human_dimension": human_dimension, "n": len(usable),
        "human_failures": labels.count(0),
        "auc": auc(scores, labels),
        "mean_score_when_human_1": (sum(s for s, y in usable if y == 1) / labels.count(1)) if labels.count(1) else None,
        "mean_score_when_human_0": (sum(s for s, y in usable if y == 0) / labels.count(0)) if labels.count(0) else None,
        "thresholds": [threshold_agreement(scores, labels, t) for t in thresholds],
    }
