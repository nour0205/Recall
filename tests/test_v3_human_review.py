"""Held-out review sheet: judge verdicts hidden, agreement computed once labelled."""
import json
from pathlib import Path
import tempfile
import unittest

from evaluation import v3_human_review as review


class V3HumanReviewTests(unittest.TestCase):
    def test_sheet_hides_the_judge_and_scores_filled_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            sheet = Path(directory) / "sheet.json"
            data = review.prepare(sheet=sheet)
            self.assertEqual(len(data["cases"]), review.SAMPLE_SIZE)
            self.assertNotIn('"judge"', json.dumps(data["cases"]))
            self.assertIsNone(review.score(sheet))  # Nothing verified yet.
            with self.assertRaises(FileExistsError):
                review.prepare(sheet=sheet)  # Never overwrites a sheet that may hold labels.
            judged = {r["question_id"]: r["judge"] for r in
                      json.loads(review.JUDGE_RUN.read_text(encoding="utf-8"))["judgments"]}
            for case in data["cases"]:  # Label exactly like the judge: agreement must be perfect.
                j = judged[case["question_id"]]
                case["labels"].update({k: j[k] for k in ("correctness", "groundedness", "citation_correctness", "refusal_correctness")})
                case["labels"]["points"] = {p["point_id"]: p["judgment"] for p in j["point_judgments"]}
                case["verified"] = True
            sheet.write_text(json.dumps(data), encoding="utf-8")
            report = review.score(sheet)
        self.assertEqual(report["labelled"], review.SAMPLE_SIZE)
        self.assertEqual(report["disagreements"], [])
        self.assertEqual(report["agreement"]["groundedness"]["agreement_rate"], 1.0)


    def test_score_counts_author_changes_to_prefilled_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            sheet = Path(directory) / "sheet.json"
            data = review.prepare(sheet=sheet)
            case = data["cases"][0]
            prefill = {"correctness": 1, "groundedness": 1, "citation_correctness": 1, "refusal_correctness": "N/A",
                       "points": {p["point_id"]: "pass" for p in case["required_points"]}, "reason": "r"}
            case["ai_prefill"] = prefill
            case["labels"].update({k: prefill[k] for k in ("correctness", "citation_correctness", "refusal_correctness")})
            case["labels"].update({"groundedness": 0, "points": dict(prefill["points"])})  # The author disagrees.
            case["verified"] = True
            sheet.write_text(json.dumps(data), encoding="utf-8")
            report = review.score(sheet)
        self.assertEqual(report["labelled"], 1)
        self.assertEqual(report["prefill_labels_changed_by_author"], [{"question_id": case["question_id"], "changed": ["groundedness"]}])


if __name__ == "__main__":
    unittest.main()
