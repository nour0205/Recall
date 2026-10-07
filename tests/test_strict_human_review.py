"""The strict-prompt workspace uses the exact baseline human-review method."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from evaluation.generation_benchmark import CASE_IDS, REFUSAL_IDS, file_hash
from evaluation import generation_human_review as review


class StrictHumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.workspace = review.create_workspace(run_path=review.STRICT_RUN_PATH)
        self.baseline_blank = review.create_workspace()
        self.baseline_review = json.loads(review.REVIEW_PATH.read_text(encoding="utf-8"))
        self.strict = json.loads(review.STRICT_RUN_PATH.read_text(encoding="utf-8"))

    def test_exact_19_ids_order_gap_and_refusal_cases(self):
        self.assertEqual(tuple(row["question_id"] for row in self.workspace["cases"]), CASE_IDS)
        self.assertNotIn("retrieval_018", CASE_IDS)
        self.assertEqual({row["question_id"] for row in self.workspace["cases"] if row["expected_behavior"] == "refuse"}, REFUSAL_IDS)

    def test_schema_rubric_and_instructions_identical_to_baseline(self):
        self.assertEqual(self.workspace.keys(), self.baseline_review.keys())
        for field in ("schema_version", "rubric", "instructions"):
            self.assertEqual(self.workspace[field], self.baseline_review[field])
        for baseline, strict in zip(self.baseline_review["cases"], self.workspace["cases"]):
            self.assertEqual(baseline.keys(), strict.keys())

    def test_references_and_required_points_exactly_match_finalized_baseline(self):
        for baseline, strict in zip(self.baseline_review["cases"], self.workspace["cases"]):
            for field in ("question_id", "question", "expected_behavior", "reference_answer", "required_points",
                          "forbidden_or_unsupported_points", "citation_expectation", "reference_review_notes"):
                self.assertEqual(strict[field], baseline[field])

    def test_contexts_mapping_and_evidence_exactly_match_frozen_baseline(self):
        baseline_raw = json.loads(review.BASELINE_PATH.read_text(encoding="utf-8"))
        for old, scored, strict in zip(baseline_raw["queries"], self.baseline_review["cases"], self.workspace["cases"]):
            for field in ("retrieved_context_chunks", "source_mapping", "required_point_evidence"):
                self.assertEqual(strict[field], old[field])
                self.assertEqual(strict[field], scored[field])
                self.assertEqual(json.dumps(strict[field], ensure_ascii=False).encode("utf-8"),
                                 json.dumps(old[field], ensure_ascii=False).encode("utf-8"))
            self.assertEqual(strict["retrieved_context_sufficient"], old["context_sufficient_for_full_answer"])

    def test_only_answers_and_prompt_run_provenance_differ_from_blank_baseline(self):
        for old, strict, raw in zip(self.baseline_blank["cases"], self.workspace["cases"], self.strict["queries"]):
            self.assertEqual(strict["generated_answer"], raw["generated_answer"])
            self.assertEqual({key: value for key, value in old.items() if key != "generated_answer"},
                             {key: value for key, value in strict.items() if key != "generated_answer"})
        for name in ("baseline", "references", "retrieval"):
            self.assertEqual(self.workspace["source_artifacts"][name], self.baseline_blank["source_artifacts"][name])
        self.assertEqual(self.workspace["source_artifacts"]["generation_run"]["prompt_version"], "grounded_strict_v1")
        self.assertEqual(self.workspace["source_artifacts"]["generation_run"]["sha256"], file_hash(review.STRICT_RUN_PATH))
        self.assertEqual(self.workspace["source_artifacts"]["prompt"]["sha256"], file_hash(review.STRICT_PROMPT_PATH))

    def test_no_quality_labels_notes_or_issues_prefilled(self):
        self.assertEqual(self.workspace["review_status"], "draft")
        for row in self.workspace["cases"]:
            for field in (*review.LABEL_FIELDS, "completeness_score", "evidence_group_coverage"):
                self.assertIsNone(row[field])
            self.assertTrue(all(point["judgment"] is None for point in row["completeness_points"]))
            for field in review.LIST_FIELDS:
                self.assertEqual(row[field], [])
            self.assertEqual(row["reviewer_notes"], "")
        self.assertNotIn("metrics", self.workspace)
        self.assertNotIn("aggregates", self.workspace)

    def test_draft_passes_and_finalized_fails_without_mutation(self):
        before = deepcopy(self.workspace)
        self.assertEqual(review.validate_workspace(self.workspace), [])
        self.assertEqual(review.validate_workspace(self.workspace, run_path=review.STRICT_RUN_PATH), [])
        errors = review.validate_workspace(self.workspace, finalized=True)
        self.assertTrue(errors)
        self.assertTrue(any("missing required-point judgment" in error for error in errors))
        self.assertEqual(before, self.workspace)

    def test_synthetic_complete_labels_follow_existing_rules(self):
        # Validator-only fixture; no labels are written to strict artifacts.
        completed = deepcopy(self.workspace)
        completed["review_status"] = "finalized"
        for row in completed["cases"]:
            for field in review.LABEL_FIELDS:
                row[field] = "N/A" if field == "prompt_compliance" else 1
            if row["expected_behavior"] == "answer":
                for point in row["completeness_points"]:
                    point["judgment"] = "pass"
                row["completeness_score"] = 1.0
                row["evidence_group_coverage"] = {gid: 1 for p in row["required_points"] for gid in p["evidence_group_ids"]}
            else:
                row["completeness_score"] = "N/A"
                row["evidence_group_coverage"] = "N/A"
        self.assertEqual(review.validate_workspace(completed), [])
        row = completed["cases"][7]
        row["completeness_points"][0]["judgment"] = "fail"
        row["completeness_score"] = 0.75
        row["evidence_group_coverage"] = {"normal_forms": 0}
        row["missing_required_points"] = [row["completeness_points"][0]["point_id"]]
        self.assertEqual(review.validate_workspace(completed), [])
        row["evidence_group_coverage"]["normal_forms"] = 1
        self.assertTrue(review.validate_workspace(completed))

    def test_invalid_labels_frozen_content_or_prompt_metadata_rejected(self):
        mutations = [
            lambda d: d["cases"][0].update(correctness=True),
            lambda d: d["cases"][0].update(groundedness="N/A"),
            lambda d: d["cases"][0].update(completeness_score=1.1),
            lambda d: d["cases"][0].update(reference_answer="changed"),
            lambda d: d["cases"][0]["required_points"][0].update(text="changed"),
            lambda d: d["cases"][0]["source_mapping"]["[S1]"].update(chunk_id="changed"),
            lambda d: d["source_artifacts"]["generation_run"].update(prompt_version="other"),
        ]
        for change in mutations:
            altered = deepcopy(self.workspace)
            change(altered)
            with self.subTest(change=change):
                self.assertTrue(review.validate_workspace(altered))

    def test_strict_run_with_changed_evidence_or_settings_rejected(self):
        mutations = [
            lambda d: d["queries"][0]["retrieved_context_chunks"][0].update(text="changed"),
            lambda d: d["queries"][0]["source_mapping"]["[S1]"].update(chunk_id="changed"),
            lambda d: d["configuration"].update(max_tokens=100),
            lambda d: d["queries"].reverse(),
            lambda d: d["queries"][0]["human_evaluation"].update(correctness=1),
            lambda d: d["queries"][0]["prompt_messages"][0].update(content="changed"),
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "strict.json"
            for change in mutations:
                altered = deepcopy(self.strict)
                change(altered)
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.subTest(change=change), self.assertRaises(ValueError):
                    review.create_workspace(run_path=path)

    def test_markdown_has_exact_strict_answers_context_and_blank_checklists(self):
        sheet = review.render_sheet(self.workspace)
        self.assertIn("# grounded_strict_v1 — Human Review", sheet)
        self.assertIn("generation_strict_prompt_v1_human_review.json", sheet)
        self.assertIn("generation_strict_prompt_v1.json", sheet)
        self.assertIn("validate evaluation/results/generation_strict_prompt_v1_human_review.json --finalized", sheet)
        self.assertEqual(sheet.count("## retrieval_"), 19)
        self.assertEqual(sheet.count("Exact retrieved context — five sources in prompt order"), 19)
        for row in self.workspace["cases"]:
            self.assertIn(review.fenced(row["generated_answer"]), sheet)
            for context in row["retrieved_context_chunks"]:
                self.assertIn(review.fenced(context["text"]), sheet)
        self.assertEqual(sheet.count("| correctness | |"), 19)

    def test_prepare_and_cli_validation_are_read_only_for_frozen_inputs(self):
        paths = (review.BASELINE_PATH, review.STRICT_RUN_PATH, review.REVIEW_PATH, review.SHEET_PATH,
                 review.REFERENCE_PATH, review.RETRIEVAL_PATH, review.STRICT_PROMPT_PATH)
        before = {path: file_hash(path) for path in paths}
        with TemporaryDirectory() as directory:
            js, md = Path(directory) / "strict_review.json", Path(directory) / "strict_review.md"
            review.prepare(js, md, run_path=review.STRICT_RUN_PATH)
            self.assertEqual(json.loads(js.read_text(encoding="utf-8")), self.workspace)
            self.assertEqual(md.read_text(encoding="utf-8"), review.render_sheet(self.workspace, review_filename=js.name))
            result = subprocess.run([sys.executable, "-m", "evaluation.generation_human_review", "validate", str(js)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            finalized = subprocess.run([sys.executable, "-m", "evaluation.generation_human_review", "validate", str(js), "--finalized"],
                                       capture_output=True, text=True, timeout=30)
            self.assertEqual(finalized.returncode, 1)
            self.assertIn("missing required-point judgment", finalized.stdout)
            self.assertEqual(json.loads(js.read_text(encoding="utf-8")), self.workspace)
            with self.assertRaises(FileExistsError):
                review.prepare(js, md, run_path=review.STRICT_RUN_PATH)
        self.assertEqual(before, {path: file_hash(path) for path in paths})


if __name__ == "__main__":
    unittest.main()
