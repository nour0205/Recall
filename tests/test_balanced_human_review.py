"""Balanced responses use the frozen manual-review methodology without scoring."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation import generation_human_review as review
from evaluation.generation_benchmark import CASE_IDS, file_hash


class BalancedHumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.workspace = review.create_workspace(run_path=review.BALANCED_RUN_PATH)

    def test_identical_schema_methodology_and_all_frozen_case_fields(self):
        self.assertEqual(tuple(r["question_id"] for r in self.workspace["cases"]), CASE_IDS)
        for prior_path in (review.REVIEW_PATH, Path("evaluation/results/generation_strict_prompt_v1_human_review.json")):
            prior = json.loads(prior_path.read_text(encoding="utf-8"))
            self.assertEqual(self.workspace.keys(), prior.keys())
            for field in ("rubric", "instructions", "schema_version"):
                self.assertEqual(self.workspace[field], prior[field])
            for old, new in zip(prior["cases"], self.workspace["cases"]):
                self.assertEqual(old.keys(), new.keys())
                for field in new.keys() - review.REVIEWER_FIELDS - {"generated_answer"}:
                    self.assertEqual(json.dumps(old[field], ensure_ascii=False).encode(),
                                     json.dumps(new[field], ensure_ascii=False).encode())
        raw = json.loads(review.BALANCED_RUN_PATH.read_text(encoding="utf-8"))
        for row, source in zip(self.workspace["cases"], raw["queries"]):
            self.assertEqual(row["generated_answer"], source["generated_answer"])
        self.assertEqual(self.workspace["source_artifacts"]["prompt"]["sha256"], file_hash(review.BALANCED_PROMPT_PATH))

    def test_blank_scores_and_draft_finalized_validation_without_mutation(self):
        before = deepcopy(self.workspace)
        for row in self.workspace["cases"]:
            for field in (*review.LABEL_FIELDS, "completeness_score", "evidence_group_coverage"):
                self.assertIsNone(row[field])
            self.assertTrue(all(p["judgment"] is None for p in row["completeness_points"]))
            self.assertEqual(row["reviewer_notes"], "")
            for field in review.LIST_FIELDS:
                self.assertEqual(row[field], [])
        self.assertEqual(review.validate_workspace(self.workspace), [])
        errors = review.validate_workspace(self.workspace, finalized=True)
        self.assertTrue(any("missing required-point judgment" in e for e in errors))
        self.assertEqual(before, self.workspace)

    def test_markdown_preserves_exact_answers_context_and_blank_checklists(self):
        sheet = review.render_sheet(self.workspace)
        self.assertIn("# grounded_balanced_v2", sheet)
        self.assertIn("../prompts/grounded_balanced_v2.json", sheet)
        self.assertIn("generation_balanced_prompt_v2_human_review.json --finalized", sheet)
        self.assertEqual(sheet.count("## retrieval_"), 19)
        self.assertEqual(sheet.count("| correctness | |"), 19)
        for row in self.workspace["cases"]:
            self.assertIn(review.fenced(row["generated_answer"]), sheet)
            for chunk in row["retrieved_context_chunks"]:
                self.assertIn(review.fenced(chunk["text"]), sheet)

    def test_prepare_preserves_historical_inputs_and_refuses_overwrite(self):
        paths = list(Path("evaluation/results").glob("*")) + list(Path("evaluation/prompts").glob("*.json"))
        paths += list(Path("app").rglob("*.py")) + [review.REFERENCE_PATH, review.RETRIEVAL_PATH]
        before = {p: file_hash(p) for p in paths if p.is_file()}
        with TemporaryDirectory() as directory:
            js, md = Path(directory)/"review.json", Path(directory)/"review.md"
            review.prepare(js, md, run_path=review.BALANCED_RUN_PATH)
            self.assertEqual(json.loads(js.read_text(encoding="utf-8")), self.workspace)
            with self.assertRaises(FileExistsError):
                review.prepare(js, md, run_path=review.BALANCED_RUN_PATH)
        self.assertEqual(before, {p: file_hash(p) for p in before})

    def test_frozen_content_and_invalid_labels_rejected(self):
        for mutation in (
            lambda w: w["cases"][0].update(correctness=True),
            lambda w: w["cases"][0].update(groundedness="N/A"),
            lambda w: w["cases"][0].update(reference_answer="changed"),
            lambda w: w["cases"][0]["source_mapping"]["[S1]"].update(chunk_id="changed"),
        ):
            changed = deepcopy(self.workspace)
            mutation(changed)
            self.assertTrue(review.validate_workspace(changed))
