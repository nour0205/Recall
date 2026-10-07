"""Deterministic checks of supplied human decisions and report arithmetic."""

import ast
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation.generation_benchmark import REFERENCE_PATH, RETRIEVAL_PATH, file_hash
from evaluation.generation_human_review import BASELINE_PATH, LABEL_FIELDS, REVIEW_PATH, validate_workspace
from evaluation import generation_report as report


ISSUES = {
    "retrieval_001": "adds overshooting, erratic updates and tuning claims not supported by supplied context",
    "retrieval_002": "adds majority/minority-class explanation and additional metric claims beyond supplied evidence",
    "retrieval_004": 'strengthens "reduce starvation" into eventual-execution/fairness guarantees not supplied by context',
    "retrieval_006": "supplies precision formula and other claims not present in supplied notes",
    "retrieval_007": "adds decomposition/data-integrity wording beyond supplied evidence",
    "retrieval_008": "adds unsupported anomaly relationship",
    "retrieval_009": "claims concurrency control is essential to maintain durability",
    "retrieval_010": "overstates prevention/concurrency-control claims",
    "retrieval_012": "adds outliers and unsupported explanatory/remedy claims",
    "retrieval_013": "adds bias/robustness/overfitting claims beyond supplied context",
    "retrieval_014": "adds unsupported claim relating 1NF to preventing anomalies",
    "retrieval_015": "adds unsupported inconsistency and false-positive significance claims",
    "retrieval_016": "adds function-call, local-variable and execution-flow explanations absent from notes",
    "retrieval_017": "adds convoy effect, starvation mitigation and general performance claims absent from supplied context",
}
REVIEW_NOTE = 'correctly refuses the unsupported F1 formula, but continues after "I don\'t know.", violating exact refusal-output behavior'


class GenerationReportTests(unittest.TestCase):
    def setUp(self):
        self.workspace = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))

    def test_all_labels_match_supplied_human_decisions_exactly(self):
        self.assertEqual(self.workspace["review_status"], "finalized")
        self.assertEqual(validate_workspace(self.workspace, finalized=True), [])
        for row in self.workspace["cases"]:
            qid = row["question_id"]
            if row["expected_behavior"] == "answer":
                label = 1 if qid in ("retrieval_003", "retrieval_011") else 0
                expected = (label, label, "N/A", label, "N/A")
                self.assertEqual(row["completeness_score"], 1.0)
                self.assertEqual(row["evidence_group_coverage"],
                                 {gid: 1 for point in row["required_points"] for gid in point["evidence_group_ids"]})
            else:
                expected = (1, 1, 1, 1, 0) if qid == "retrieval_019" else ("N/A", 1, 1, "N/A", 1)
                self.assertEqual(row["completeness_score"], "N/A")
                self.assertEqual(row["evidence_group_coverage"], "N/A")
            self.assertEqual(tuple(row[field] for field in LABEL_FIELDS), expected)
            self.assertTrue(all(point["judgment"] == "pass" for point in row["completeness_points"]))
            self.assertEqual(row["unsupported_claims"], [ISSUES[qid]] if qid in ISSUES else [])
            self.assertEqual(row["reviewer_notes"], REVIEW_NOTE if qid == "retrieval_019" else "")
            self.assertEqual(row["missing_required_points"], [])
            self.assertEqual(row["citation_issues"], [])

    def test_exact_per_dimension_denominators_and_rates(self):
        metrics = report.aggregate_review(self.workspace)["metrics"]
        expected = {"correctness": (3, 17), "groundedness": (5, 19),
                    "refusal_correctness": (3, 3), "citation_correctness": (3, 17),
                    "prompt_compliance": (2, 3), "full_completeness_rate": (16, 16)}
        for field, (passed, eligible) in expected.items():
            with self.subTest(field=field):
                self.assertEqual(metrics[field]["passed_count"], passed)
                self.assertEqual(metrics[field]["eligible_count"], eligible)
                self.assertEqual(metrics[field]["excluded_na_count"], 19 - eligible)
                self.assertEqual(metrics[field]["value"], passed / eligible)
                self.assertEqual(metrics[field]["failed_count"], eligible - passed)
        self.assertEqual(metrics["mean_completeness"]["value"], 1.0)
        self.assertEqual(metrics["mean_completeness"]["eligible_count"], 16)
        self.assertEqual(metrics["mean_completeness"]["score_sum"], 16.0)

    def test_case_019_inclusion_is_dimension_specific(self):
        metrics = report.aggregate_review(self.workspace)["metrics"]
        for field in ("correctness", "groundedness", "citation_correctness", "refusal_correctness", "prompt_compliance"):
            self.assertIn("retrieval_019", metrics[field]["eligible_question_ids"])
        self.assertNotIn("retrieval_019", metrics["mean_completeness"]["eligible_question_ids"])
        self.assertNotIn("retrieval_005", metrics["correctness"]["eligible_question_ids"])
        self.assertNotIn("retrieval_020", metrics["citation_correctness"]["eligible_question_ids"])

    def test_failure_counts_categories_and_exact_notes(self):
        failures = report.aggregate_review(self.workspace)["failures"]
        self.assertEqual(failures["dimension_failed_counts"], {
            "correctness": 14, "groundedness": 14, "refusal_correctness": 0,
            "citation_correctness": 14, "prompt_compliance": 1, "incomplete_answers": 0,
        })
        self.assertEqual(failures["unique_failed_case_count"], 15)
        categories = {entry["category"]: entry for entry in failures["categories"]}
        self.assertEqual(categories["unsupported elaboration / over-generation"]["case_count"], 14)
        self.assertEqual(set(categories["unsupported elaboration / over-generation"]["question_ids"]), set(ISSUES))
        self.assertEqual(categories["refusal output-format noncompliance"]["question_ids"], ["retrieval_019"])
        notes = {entry["question_id"]: entry for entry in failures["reviewer_issue_details"]}
        for qid, issue in ISSUES.items():
            self.assertEqual(notes[qid]["unsupported_claims"], [issue])
        self.assertEqual(notes["retrieval_019"]["reviewer_notes"], REVIEW_NOTE)

    def test_aggregation_never_mutates_labels(self):
        original = deepcopy(self.workspace)
        report.aggregate_review(self.workspace)
        self.assertEqual(self.workspace, original)

    def test_draft_and_invalid_labels_block_aggregation(self):
        draft = deepcopy(self.workspace)
        draft["review_status"] = "draft"
        with self.assertRaises(ValueError):
            report.aggregate_review(draft)
        mutations = [lambda row: row.update(groundedness=None), lambda row: row.update(correctness=True),
                     lambda row: row.update(completeness_score=0.5),
                     lambda row: row["completeness_points"][0].update(judgment=None)]
        for change in mutations:
            invalid = deepcopy(self.workspace)
            change(invalid["cases"][0])
            with self.subTest(change=change), self.assertRaises(ValueError):
                report.aggregate_review(invalid)

    def test_partial_completeness_uses_case_mean_and_full_point_denominator(self):
        # Synthetic arithmetic fixture, never written to the actual human review.
        changed = deepcopy(self.workspace)
        row = changed["cases"][7]
        row["completeness_points"][0]["judgment"] = "fail"
        row["completeness_score"] = 0.75
        row["evidence_group_coverage"] = {"normal_forms": 0}
        row["missing_required_points"] = [row["completeness_points"][0]["point_id"]]
        metrics = report.aggregate_review(changed)["metrics"]
        self.assertEqual(metrics["mean_completeness"]["value"], 15.75 / 16)
        self.assertEqual(metrics["full_completeness_rate"]["value"], 15 / 16)
        self.assertEqual(metrics["full_completeness_rate"]["eligible_count"], 16)

    def test_zero_eligible_dimension_is_null_not_zero(self):
        changed = deepcopy(self.workspace)
        for row in changed["cases"]:
            row["prompt_compliance"] = "N/A"
        metric = report.aggregate_review(changed)["metrics"]["prompt_compliance"]
        self.assertIsNone(metric["value"])
        self.assertEqual(metric["eligible_count"], 0)
        self.assertEqual(metric["excluded_na_count"], 19)

    def test_latency_usage_configuration_and_hashes_copied_from_frozen_inputs(self):
        summary = report.build_summary()
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        for field in ("generation_latency_seconds", "token_usage"):
            self.assertEqual(summary[field], baseline["operational_summary"][field])
        self.assertEqual(summary["generation_configuration"], baseline["configuration"])
        self.assertEqual(summary["api_runtime_failures"], [])
        self.assertEqual(summary["case_counts"], {"total": 19, "answerable": 16, "refusal": 3,
                                                "answerable_with_sufficient_context": 16, "completed_generations": 19})
        self.assertEqual(summary["human_review_artifact"]["sha256"], file_hash(REVIEW_PATH))
        self.assertEqual(summary["frozen_source_artifacts"], self.workspace["source_artifacts"])

    def test_report_deterministic_and_contains_no_weighted_score(self):
        first, second = report.build_summary(), report.build_summary()
        self.assertEqual(first, second)
        self.assertEqual(report.render_summary(first), report.render_summary(second))
        self.assertEqual(set(first["metrics"]), {*LABEL_FIELDS, "mean_completeness", "full_completeness_rate"})
        sheet = report.render_summary(first)
        for expected in ("3/17 (17.65%)", "5/19 (26.32%)", "16/16 (100.00%)", "2/3 (66.67%)",
                         "unsupported elaboration / over-generation", "25,747"):
            self.assertIn(expected, sheet)

    def test_writing_report_preserves_inputs_and_refuses_overwrite(self):
        paths = (REVIEW_PATH, BASELINE_PATH, REFERENCE_PATH, RETRIEVAL_PATH)
        before = {path: file_hash(path) for path in paths}
        with TemporaryDirectory() as directory:
            js, md = Path(directory) / "summary.json", Path(directory) / "summary.md"
            expected = report.write_report(summary_path=js, markdown_path=md)
            self.assertEqual(json.loads(js.read_text(encoding="utf-8")), expected)
            self.assertEqual(md.read_text(encoding="utf-8"), report.render_summary(expected))
            prior = (js.read_bytes(), md.read_bytes())
            with self.assertRaises(FileExistsError):
                report.write_report(summary_path=js, markdown_path=md)
            self.assertEqual(prior, (js.read_bytes(), md.read_bytes()))
        self.assertEqual(before, {path: file_hash(path) for path in paths})

    def test_report_has_no_model_production_or_generation_runner_imports(self):
        tree = ast.parse(Path(report.__file__).read_text(encoding="utf-8"))
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.append(node.module)
        self.assertTrue(all(not name.startswith(("app.", "openai", "ragas")) for name in names))
        self.assertNotIn("evaluation.run_generation_baseline", names)


if __name__ == "__main__":
    unittest.main()
