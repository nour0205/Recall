"""Offline review-workspace checks. Filled labels below are synthetic fixtures.

These tests never review answer quality or write labels to the actual artifact.
"""

import ast
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation.generation_benchmark import CASE_IDS, REFUSAL_IDS, REFERENCE_PATH, RETRIEVAL_PATH, file_hash
from evaluation import generation_human_review as review


def synthetic_completed_workspace():
    """Invented labels exercise validation only; they are not answer judgments."""
    workspace = review.create_workspace()
    workspace["review_status"] = "finalized"
    for row in workspace["cases"]:
        for field in review.LABEL_FIELDS:
            row[field] = "N/A" if field == "prompt_compliance" else 1
        if row["expected_behavior"] == "answer":
            for point in row["completeness_points"]:
                point["judgment"] = "pass"
            row["completeness_score"] = 1.0
            row["evidence_group_coverage"] = {
                gid: 1 for point in row["required_points"] for gid in point["evidence_group_ids"]
            }
        else:
            row["completeness_score"] = "N/A"
            row["evidence_group_coverage"] = "N/A"
    return workspace


class HumanReviewWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.workspace = review.create_workspace()

    def test_exact_19_cases_and_three_refusals(self):
        self.assertEqual(tuple(row["question_id"] for row in self.workspace["cases"]), CASE_IDS)
        self.assertNotIn("retrieval_018", CASE_IDS)
        self.assertEqual({row["question_id"] for row in self.workspace["cases"]
                          if row["expected_behavior"] == "refuse"}, REFUSAL_IDS)
        self.assertEqual(sum(row["retrieved_context_sufficient"] is True for row in self.workspace["cases"]), 16)

    def test_all_reviewer_fields_empty_and_no_aggregates(self):
        for row in self.workspace["cases"]:
            for field in (*review.LABEL_FIELDS, "completeness_score", "evidence_group_coverage"):
                self.assertIsNone(row[field])
            self.assertTrue(all(point["judgment"] is None for point in row["completeness_points"]))
            for field in review.LIST_FIELDS:
                self.assertEqual(row[field], [])
            self.assertEqual(row["reviewer_notes"], "")
        self.assertNotIn("aggregates", self.workspace)

    def test_verbatim_answers_context_and_reference_fields(self):
        _, refs, baseline = review.frozen_inputs()
        for row, ref, raw in zip(self.workspace["cases"], refs.cases, baseline["queries"]):
            self.assertEqual(row["question"], raw["question"])
            self.assertEqual(row["generated_answer"], raw["generated_answer"])
            self.assertEqual(row["reference_answer"], ref.reference_answer)
            self.assertEqual(row["retrieved_context_chunks"], raw["retrieved_context_chunks"])
            self.assertEqual(row["source_mapping"], raw["source_mapping"])
            self.assertEqual(row["required_point_evidence"], raw["required_point_evidence"])
            self.assertEqual(row["required_points"], [p.model_dump(exclude_none=True) for p in ref.required_points])

    def test_draft_valid_and_validation_never_mutates(self):
        original = deepcopy(self.workspace)
        self.assertEqual(review.validate_workspace(self.workspace), [])
        self.assertEqual(self.workspace, original)
        self.assertTrue(review.validate_workspace(self.workspace, finalized=True))
        self.assertEqual(self.workspace, original)

    def test_synthetic_finalized_valid(self):
        self.assertEqual(review.validate_workspace(synthetic_completed_workspace()), [])

    def test_forced_finalized_requires_completed_labels(self):
        errors = review.validate_workspace(self.workspace, finalized=True)
        self.assertTrue(any("correctness" in error for error in errors))
        self.assertTrue(any("missing required-point judgment" in error for error in errors))
        self.assertTrue(any("completeness_score" in error for error in errors))
        self.assertTrue(any("evidence_group_coverage" in error for error in errors))
        self.workspace["review_status"] = "finalized"
        self.assertTrue(review.validate_workspace(self.workspace))

    def test_binary_labels_are_strict_and_allow_na_except_groundedness(self):
        for field in review.LABEL_FIELDS:
            for invalid in (True, False, 1.0, "1", "pass", -1, 2, [], {}):
                changed = deepcopy(self.workspace)
                changed["cases"][0][field] = invalid
                with self.subTest(field=field, invalid=invalid):
                    self.assertTrue(review.validate_workspace(changed))
            for valid in (0, 1):
                changed = deepcopy(self.workspace)
                changed["cases"][0][field] = valid
                self.assertEqual(review.validate_workspace(changed), [])
            changed = deepcopy(self.workspace)
            changed["cases"][0][field] = "N/A"
            self.assertEqual(bool(review.validate_workspace(changed)), field == "groundedness")

    def test_completeness_range_type_and_finiteness(self):
        for invalid in (-0.1, 1.1, True, "0.5", "N/A", float("nan"), float("inf"), 10**400):
            changed = deepcopy(self.workspace)
            changed["cases"][0]["completeness_score"] = invalid
            with self.subTest(value=invalid):
                self.assertTrue(review.validate_workspace(changed))
        for valid in (0, 0.5, 1):
            changed = deepcopy(self.workspace)
            changed["cases"][0]["completeness_score"] = valid
            self.assertEqual(review.validate_workspace(changed), [])

    def test_point_ids_and_judgments_validated(self):
        mutations = [
            lambda row: row["completeness_points"].pop(),
            lambda row: row["completeness_points"].append(deepcopy(row["completeness_points"][0])),
            lambda row: row["completeness_points"][0].update(point_id="unknown"),
            lambda row: row["completeness_points"][0].update(judgment=1),
            lambda row: row["completeness_points"][0].update(judgment="N/A"),
            lambda row: row["completeness_points"][0].update(extra="field"),
        ]
        for change in mutations:
            changed = deepcopy(self.workspace)
            change(changed["cases"][0])
            with self.subTest(change=change):
                self.assertTrue(review.validate_workspace(changed))

    def test_partial_human_labels_and_compound_group_consistency(self):
        workspace = synthetic_completed_workspace()
        row = workspace["cases"][7]  # Four points in one evidence group.
        row["completeness_points"][0]["judgment"] = "fail"
        row["completeness_score"] = 0.75
        row["evidence_group_coverage"] = {"normal_forms": 0}
        row["missing_required_points"] = [row["completeness_points"][0]["point_id"]]
        self.assertEqual(review.validate_workspace(workspace), [])
        row["completeness_score"] = 1
        self.assertTrue(any("disagrees" in error for error in review.validate_workspace(workspace)))
        row["completeness_score"] = 0.75
        row["evidence_group_coverage"]["normal_forms"] = 1
        self.assertTrue(any("normal_forms" in error for error in review.validate_workspace(workspace)))

    def test_group_keys_and_values_validated(self):
        for invalid in (0.5, {"unknown": 1}, {"learning_rate": True}, {"learning_rate": 1.0}):
            changed = deepcopy(self.workspace)
            changed["cases"][0]["evidence_group_coverage"] = invalid
            with self.subTest(value=invalid):
                self.assertTrue(review.validate_workspace(changed))

    def test_missing_points_and_issue_fields_validated(self):
        workspace = synthetic_completed_workspace()
        row = workspace["cases"][0]
        row["completeness_points"][0]["judgment"] = "fail"
        row["completeness_score"] = 0
        row["evidence_group_coverage"] = {"learning_rate": 0}
        self.assertTrue(any("missing_required_points" in error for error in review.validate_workspace(workspace)))
        row["missing_required_points"] = ["divergence"]
        self.assertEqual(review.validate_workspace(workspace), [])
        for field in review.LIST_FIELDS:
            row[field] = [{}]
            self.assertTrue(review.validate_workspace(workspace))
            row[field] = []

    def test_refusal_completeness_na_and_optional_prompt_compliance(self):
        workspace = synthetic_completed_workspace()
        refusal = workspace["cases"][4]
        self.assertIsNone(refusal["completeness_points"][0]["judgment"])
        self.assertEqual(review.validate_workspace(workspace), [])
        refusal["completeness_score"] = 1
        self.assertTrue(review.validate_workspace(workspace))
        refusal["completeness_score"] = "N/A"
        refusal["evidence_group_coverage"] = {}
        self.assertTrue(review.validate_workspace(workspace))

    def test_frozen_content_and_provenance_cannot_change(self):
        mutations = [
            lambda d: d["cases"][0].update(question="edited"),
            lambda d: d["cases"][0].update(generated_answer="edited"),
            lambda d: d["cases"][0].update(reference_answer="edited"),
            lambda d: d["cases"][0].update(retrieved_context_sufficient=False),
            lambda d: d["cases"][0]["retrieved_context_chunks"][0].update(text="edited"),
            lambda d: d["cases"][0]["source_mapping"]["[S1]"].update(chunk_id="edited"),
            lambda d: d["source_artifacts"]["baseline"].update(sha256="edited"),
            lambda d: d["rubric"]["correctness"].update(rule="edited"),
        ]
        for change in mutations:
            changed = deepcopy(self.workspace)
            change(changed)
            with self.subTest(change=change):
                self.assertTrue(review.validate_workspace(changed))

    def test_duplicates_missing_or_reordered_cases_rejected(self):
        for change in (lambda cases: cases.pop(), lambda cases: cases.reverse(),
                       lambda cases: cases.append(deepcopy(cases[0]))):
            changed = deepcopy(self.workspace)
            change(changed["cases"])
            self.assertTrue(review.validate_workspace(changed))

    def test_malformed_workspace_produces_errors(self):
        for invalid in (None, [], {"cases": None}, {"cases": ["invalid"]}):
            self.assertTrue(review.validate_workspace(invalid))

    def test_markdown_has_all_cases_and_verbatim_context_and_answers(self):
        sheet = review.render_sheet(self.workspace)
        self.assertEqual(sheet.count("## retrieval_"), 19)
        self.assertEqual(sheet.count("Exact retrieved context — five sources in prompt order"), 19)
        for row in self.workspace["cases"]:
            self.assertIn(row["question"], sheet)
            self.assertIn(review.fenced(row["generated_answer"]), sheet)
            for context in row["retrieved_context_chunks"]:
                self.assertIn(review.fenced(context["text"]), sheet)
                self.assertIn(f"**{context['source_label']}** · document `{context['document_id']}` · chunk `{context['chunk_id']}`", sheet)
        self.assertIn("| correctness | |", sheet)
        self.assertNotIn("| correctness | 1 |", sheet)

    def test_fences_preserve_markdown_content_literally(self):
        text = "## Heading\n```python\nprint('example')\n```\n"
        block = review.fenced(text)
        self.assertTrue(block.startswith("````text\n"))
        self.assertIn(text, block)
        self.assertTrue(block.endswith("````"))

    def test_prepare_exclusive_and_frozen_inputs_unchanged(self):
        inputs = (review.BASELINE_PATH, REFERENCE_PATH, RETRIEVAL_PATH)
        before = {path: file_hash(path) for path in inputs}
        with TemporaryDirectory() as directory:
            json_path, md_path = Path(directory) / "review.json", Path(directory) / "review.md"
            review.prepare(json_path, md_path)
            self.assertEqual(review.validate_workspace(json.loads(json_path.read_text(encoding="utf-8"))), [])
            prior = (json_path.read_bytes(), md_path.read_bytes())
            with self.assertRaises(FileExistsError):
                review.prepare(json_path, md_path)
            self.assertEqual(prior, (json_path.read_bytes(), md_path.read_bytes()))
        self.assertEqual(before, {path: file_hash(path) for path in inputs})

    def test_helper_has_no_model_runner_or_production_imports(self):
        tree = ast.parse(Path(review.__file__).read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module)
        self.assertTrue(all(not name.startswith(("app.", "openai", "ragas")) for name in imported))
        self.assertNotIn("evaluation.run_generation_baseline", imported)


if __name__ == "__main__":
    unittest.main()
