"""Validate and render the draft v3 benchmark (evaluation/drafts/benchmark_v3_draft.json).

    python -m evaluation.benchmark_draft            # validate
    python -m evaluation.benchmark_draft --render   # also write a review sheet next to the draft

Validation guarantees that every evidence quote appears word for word in the
cited demo note, so no evidence can be invented. It makes no API calls.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

DRAFT = Path("evaluation/drafts/benchmark_v3_draft.json")
NOTES = Path("demo_notes")


def load(path=DRAFT) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def note_texts(notes_dir=NOTES) -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8").strip() for p in Path(notes_dir).glob("*.txt")}


def validate(draft: dict, notes: dict[str, str]) -> list[str]:
    problems = []
    ids = [c["question_id"] for c in draft["cases"]]
    problems += [f"duplicate question_id {i}" for i, n in Counter(ids).items() if n > 1]
    questions = [c["question"].strip().lower() for c in draft["cases"]]
    problems += [f"duplicate question: {q}" for q, n in Counter(questions).items() if n > 1]

    def check_quotes(case_id, evidence):
        for item in evidence:
            text = notes.get(item["document_id"])
            if text is None:
                problems.append(f"{case_id}: unknown note {item['document_id']}")
            elif item["quote"] not in text:
                problems.append(f"{case_id}: quote not found in {item['document_id']}: {item['quote']!r}")

    for case in draft["cases"]:
        cid = case["question_id"]
        if case["category"] not in draft["categories"]:
            problems.append(f"{cid}: unknown category {case['category']}")
        if case["expected_behavior"] == "answer":
            if not case["required_points"]:
                problems.append(f"{cid}: answer case without required points")
            point_ids = [p["point_id"] for p in case["required_points"]]
            if len(point_ids) != len(set(point_ids)):
                problems.append(f"{cid}: duplicate point_id")
            for point in case["required_points"]:
                if not point["evidence"]:
                    problems.append(f"{cid}/{point['point_id']}: no evidence")
                check_quotes(f"{cid}/{point['point_id']}", point["evidence"])
        elif case["expected_behavior"] == "refuse":
            if case["required_points"]:
                problems.append(f"{cid}: refuse case with required points")
            if case["reference_answer"] != "I don't know.":
                problems.append(f"{cid}: refuse case reference must be exactly I don't know.")
            check_quotes(cid, case.get("closest_evidence", []))
        else:
            problems.append(f"{cid}: unknown expected_behavior")
    return problems


def render(draft: dict) -> str:
    counts = Counter(c["category"] for c in draft["cases"])
    lines = ["# Benchmark v3 draft: review sheet", "",
             "Generated from `benchmark_v3_draft.json` by `python -m evaluation.benchmark_draft --render`; edit the JSON, not this file.", "",
             "For each question, check: is it clear, is the reference answer right, are the required points the right ones, "
             "and for refuse cases, are the notes really silent on it?", "",
             "| Category | Questions | Tests |", "|---|---:|---|"]
    lines += [f"| {name} | {counts.get(name, 0)} | {desc} |" for name, desc in draft["categories"].items()]
    lines += ["", f"**Total:** {len(draft['cases'])} ({sum(c['expected_behavior'] == 'answer' for c in draft['cases'])} answerable, "
              f"{sum(c['expected_behavior'] == 'refuse' for c in draft['cases'])} refusals)"]
    for case in draft["cases"]:
        lines += ["", f"## {case['question_id']} · {case['category']} · {case['expected_behavior']}", "",
                  f"**Q:** {case['question']}", "", f"**Reference:** {case['reference_answer']}"]
        for point in case["required_points"]:
            lines.append(f"- `{point['point_id']}`: {point['text']}")
            lines += [f"  - {e['document_id']}: \"{e['quote']}\"" for e in point["evidence"]]
        if case["expected_behavior"] == "refuse" and case.get("closest_evidence"):
            lines.append("- Closest the notes come:")
            lines += [f"  - {e['document_id']}: \"{e['quote']}\"" for e in case["closest_evidence"]]
        lines += ["", f"*Notes:* {case['review_notes']}"]
    return "\n".join(lines) + "\n"


def main(write_sheet=False):
    draft = load()
    problems = validate(draft, note_texts())
    if problems:
        raise SystemExit("Invalid draft:\n" + "\n".join(problems))
    print(f"Valid: {len(draft['cases'])} questions; every evidence quote found verbatim in its note.")
    if write_sheet:
        sheet = DRAFT.with_name("benchmark_v3_review.md")
        sheet.write_text(render(draft), encoding="utf-8")
        print(f"Review sheet: {sheet}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--render", action="store_true")
    main(parser.parse_args().render)
