"""Aggregation checks use supplied labels, never generated-answer inspection."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from evaluation.generation_human_review import validate_workspace
from evaluation.generation_report import aggregate_review
from evaluation import generation_prompt_comparison as comparison


class PromptComparisonTests(unittest.TestCase):
    def test_strict_metrics_preserve_false_refusal_denominators_and_exact_points(self):
        report = comparison.build_comparison()
        strict = report["experiments"]["grounded_strict_v1"]
        metrics = strict["metrics"]
        for key, numerator, denominator in (
            ("correctness", 14, 15), ("groundedness", 19, 19),
            ("citation_correctness", 15, 15), ("refusal_correctness", 3, 4),
            ("prompt_compliance", 3, 4), ("full_completeness_rate", 12, 16)):
            self.assertEqual(metrics[key]["passed_count"], numerator)
            self.assertEqual(metrics[key]["eligible_count"], denominator)
        self.assertEqual(metrics["mean_completeness"]["score_sum"], 13.5)
        self.assertEqual(metrics["mean_completeness"]["eligible_count"], 16)
        self.assertEqual(strict["failures"]["unique_failed_case_count"], 4)
        self.assertFalse(any(c["category"] == "unsupported elaboration / over-generation" for c in strict["failures"]["categories"]))
        for transition in report["case_transitions"]:
            for name, stem in comparison.SOURCES.items():
                review = json.loads((comparison.RESULTS/(stem+"_human_review.json")).read_text(encoding="utf-8"))
                source = next(r for r in review["cases"] if r["question_id"] == transition["question_id"])
                for key, value in transition["experiments"][name].items():
                    self.assertEqual(value, source[key])

    def test_three_way_report_is_deterministic_and_does_not_mutate_inputs(self):
        paths = list(comparison.RESULTS.glob("*.json")) + list(Path("app").rglob("*.py"))
        from evaluation.generation_benchmark import file_hash
        before = {p: file_hash(p) for p in paths}
        first = comparison.build_comparison()
        self.assertEqual(first, comparison.build_comparison())
        self.assertEqual(first["experiments"]["generation_baseline_v1"]["metrics"]["correctness"]["passed_count"], 3)
        self.assertIn("no statistical significance", first["limitation"])
        with TemporaryDirectory() as directory:
            js, md = Path(directory)/"comparison.json", Path(directory)/"comparison.md"
            saved = comparison.write_comparison(js, md)
            self.assertEqual(json.loads(js.read_text(encoding="utf-8")), first)
            sheet = md.read_text(encoding="utf-8")
            self.assertEqual(sheet, comparison.render_comparison(saved))
            self.assertEqual(sheet.count("| retrieval_"), 9)
            self.assertIn("including the failed refusal", sheet)
            self.assertIn("refusal correctness / prompt compliance", sheet)
        self.assertEqual(before, {p: file_hash(p) for p in paths})

    def test_balanced_review_matches_exact_supplied_decisions_and_metrics(self):
        review = json.loads((comparison.RESULTS / "generation_balanced_prompt_v2_human_review.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_workspace(review, finalized=True), [])
        metrics = aggregate_review(review)["metrics"]
        for key, numerator, denominator in (
            ("correctness", 11, 16), ("groundedness", 15, 19),
            ("citation_correctness", 12, 16), ("refusal_correctness", 3, 3),
            ("prompt_compliance", 3, 3), ("full_completeness_rate", 15, 16)):
            self.assertEqual(metrics[key]["passed_count"], numerator)
            self.assertEqual(metrics[key]["eligible_count"], denominator)
        self.assertEqual(metrics["mean_completeness"]["score_sum"], 15.5)
        self.assertEqual(metrics["mean_completeness"]["eligible_count"], 16)
        issues = [r["question_id"] for r in review["cases"] if r["unsupported_claims"]]
        self.assertEqual(issues, ["retrieval_007", "retrieval_013", "retrieval_014", "retrieval_017"])
        row = next(r for r in review["cases"] if r["question_id"] == "retrieval_008")
        self.assertEqual(row["missing_required_points"], ["partial_definition", "transitive_definition"])

    def test_unfinalized_review_is_not_reconstructed_from_aggregate_totals(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "generation_baseline_v1_human_review.json"
            draft = json.loads((comparison.RESULTS / path.name).read_text(encoding="utf-8"))
            draft["review_status"] = "draft"
            path.write_text(json.dumps(draft), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "finalized"):
                comparison.build_comparison(directory)

    def test_failed_validation_creates_no_official_outputs(self):
        with TemporaryDirectory() as directory:
            js, md = Path(directory)/"report.json", Path(directory)/"report.md"
            with patch.object(comparison, "build_comparison", side_effect=ValueError("Missing finalized labels")):
                with self.assertRaises(ValueError):
                    comparison.write_comparison(js, md)
            self.assertFalse(js.exists())
            self.assertFalse(md.exists())

    def test_existing_report_is_preserved(self):
        with TemporaryDirectory() as directory:
            js, md = Path(directory)/"report.json", Path(directory)/"report.md"
            js.write_text("historical", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                comparison.write_comparison(js, md)
            self.assertEqual(js.read_text(encoding="utf-8"), "historical")
