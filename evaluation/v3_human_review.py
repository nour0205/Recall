"""Held-out test of the judge: human labels for a random sample of v3 answers.

    python -m evaluation.v3_human_review prepare   # write the labelling sheet (judge verdicts hidden)
    python -m evaluation.v3_human_review score     # agreement between your labels and the judge

The sample is drawn at random (fixed seed) from the answers the model judge
labelled in the v3 pilot run, so the judge's verdicts on these answers were
never used to write its conventions. Fill in the label fields of the JSON
sheet; the Markdown sheet is for reading. No API calls.
"""
import argparse
import json
from pathlib import Path
import random

from evaluation.judge_agreement import compare, disagreements

JUDGE_RUN = Path("evaluation/results/judge_end_to_end_judge_v2_20261013T145257Z.json")
SHEET = Path("evaluation/drafts/v3_human_review_sample.json")
SAMPLE_SIZE = 20
SEED = 13

LABEL_HELP = {
    "correctness": "1 if every claim is accurate according to the notes, 0 if any claim is wrong or cannot be validated, N/A for a pure refusal",
    "groundedness": "1 if every claim follows from the supplied sources, 0 if anything is added (including a dropped may/usually/often)",
    "citation_correctness": "1 if every claim has a citation to a source that supports it (a trailing citation may cover a short paragraph), else 0; N/A for a pure refusal",
    "refusal_correctness": "N/A when an answerable question was answered; otherwise 1 for a justified refusal, 0 for a wrong one",
    "points": "pass or fail for each required point",
}


def prepare(judge_run=JUDGE_RUN, sheet=SHEET, size=SAMPLE_SIZE, seed=SEED):
    run = json.loads(Path(judge_run).read_text(encoding="utf-8"))
    judged = [r for r in run["judgments"] if not r["judge_meta"].get("deterministic")]
    sample = sorted(random.Random(seed).sample(judged, size), key=lambda r: r["question_id"])
    cases = [{
        "question_id": r["question_id"], "question": r["question"], "expected_behavior": r["expected_behavior"],
        "sources": [{"label": f"[S{i}]", **s} for i, s in enumerate(r["sources"], 1)],
        "answer": r["answer"], "reference_answer": r["reference_answer"], "case_notes": r["case_notes"],
        "required_points": [{"point_id": p["point_id"], "text": p["text"]} for p in r["required_points"]],
        "labels": {"correctness": None, "groundedness": None, "citation_correctness": None, "refusal_correctness": None,
                   "points": {p["point_id"]: None for p in r["required_points"]}, "notes": ""},
    } for r in sample]
    data = {"judge_run": Path(judge_run).as_posix(), "seed": seed, "label_help": LABEL_HELP, "cases": cases}
    Path(sheet).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(sheet).with_suffix(".md").write_text(render(data), encoding="utf-8")
    return data


def render(data) -> str:
    lines = ["# v3 held-out review: labelling sheet", "",
             "Label each answer in `v3_human_review_sample.json` (fields under `labels`). The judge's verdicts are hidden on purpose.", "",
             "| Label | Meaning |", "|---|---|"]
    lines += [f"| `{k}` | {v} |" for k, v in data["label_help"].items()]
    for case in data["cases"]:
        lines += ["", f"## {case['question_id']}", "", f"**Q:** {case['question']}", "", "**Sources the model saw:**", ""]
        lines += [f"- {s['label']} *{s['document_id']}*: {s['text']}" for s in case["sources"]]
        lines += ["", f"**Answer:** {case['answer']}", "", "**Required points:**"]
        lines += [f"- `{p['point_id']}`: {p['text']}" for p in case["required_points"]]
        lines += ["", f"*Reference:* {case['reference_answer']}  ", f"*Case notes:* {case['case_notes']}"]
    return "\n".join(lines) + "\n"


def score(sheet=SHEET):
    data = json.loads(Path(sheet).read_text(encoding="utf-8"))
    judged = {r["question_id"]: r for r in json.loads(Path(data["judge_run"]).read_text(encoding="utf-8"))["judgments"]}
    cases, missing = [], []
    for case in data["cases"]:
        labels = case["labels"]
        if any(labels[k] is None for k in ("correctness", "groundedness", "citation_correctness", "refusal_correctness")) \
                or any(v not in ("pass", "fail") for v in labels["points"].values()):
            missing.append(case["question_id"])
            continue
        points = [{"point_id": pid, "judgment": labels["points"][pid]} for pid in labels["points"]]
        judge = judged[case["question_id"]]
        cases.append({
            "run": "v3_heldout", "question_id": case["question_id"], "expected_behavior": case["expected_behavior"],
            "human": {**{k: labels[k] for k in ("correctness", "groundedness", "citation_correctness", "refusal_correctness")},
                      "completeness_points": points,
                      "completeness_score": sum(p["judgment"] == "pass" for p in points) / len(points)},
            "judge": judge["judge"], "judge_completeness_score": judge["judge_completeness_score"],
        })
    if missing:
        print(f"Not yet labelled (skipped): {', '.join(missing)}")
    if not cases:
        return None
    report = {"labelled": len(cases), "agreement": compare(cases), "disagreements": disagreements(cases)}
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["prepare", "score"])
    args = parser.parse_args()
    if args.command == "prepare":
        data = prepare()
        print(f"Wrote {SHEET} and {SHEET.with_suffix('.md')} ({len(data['cases'])} answers).")
    else:
        score()
