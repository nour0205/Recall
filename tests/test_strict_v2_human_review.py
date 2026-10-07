"""Strict v2 uses unchanged manual review with no inferred quality labels."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation import generation_human_review as review
from evaluation.generation_benchmark import CASE_IDS, file_hash


class StrictV2HumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.workspace = review.create_workspace(run_path=review.STRICT_V2_RUN_PATH)

    def test_all_19_cases_match_every_previous_review_and_only_answers_differ(self):
        self.assertEqual(tuple(r['question_id'] for r in self.workspace['cases']), CASE_IDS)
        for stem in ('generation_baseline_v1', 'generation_strict_prompt_v1', 'generation_balanced_prompt_v2'):
            prior = json.loads(Path('evaluation/results', stem+'_human_review.json').read_text(encoding='utf-8'))
            self.assertEqual(prior.keys(), self.workspace.keys())
            for key in ('schema_version', 'rubric', 'instructions'):
                self.assertEqual(prior[key], self.workspace[key])
            for old, new in zip(prior['cases'], self.workspace['cases']):
                self.assertEqual(old.keys(), new.keys())
                for key in new.keys() - review.REVIEWER_FIELDS - {'generated_answer'}:
                    self.assertEqual(json.dumps(old[key], ensure_ascii=False).encode(), json.dumps(new[key], ensure_ascii=False).encode())
        raw = json.loads(review.STRICT_V2_RUN_PATH.read_text(encoding='utf-8'))
        for new, source in zip(self.workspace['cases'], raw['queries']):
            self.assertEqual(new['generated_answer'], source['generated_answer'])
        for previous in (review.create_workspace(), review.create_workspace(run_path=review.STRICT_RUN_PATH), review.create_workspace(run_path=review.BALANCED_RUN_PATH)):
            for old, new in zip(previous['cases'], self.workspace['cases']):
                self.assertEqual({k:v for k,v in old.items() if k!='generated_answer'}, {k:v for k,v in new.items() if k!='generated_answer'})

    def test_labels_blank_and_draft_passes_finalized_fails_without_mutation(self):
        before = deepcopy(self.workspace)
        for row in self.workspace['cases']:
            for key in (*review.LABEL_FIELDS, 'completeness_score', 'evidence_group_coverage'):
                self.assertIsNone(row[key])
            self.assertTrue(all(p['judgment'] is None for p in row['completeness_points']))
            for key in review.LIST_FIELDS:
                self.assertEqual(row[key], [])
            self.assertEqual(row['reviewer_notes'], '')
        self.assertEqual(review.validate_workspace(self.workspace), [])
        self.assertEqual(review.validate_workspace(self.workspace, run_path=review.STRICT_V2_RUN_PATH), [])
        self.assertTrue(any('missing required-point judgment' in e for e in review.validate_workspace(self.workspace, finalized=True)))
        self.assertEqual(before, self.workspace)

    def test_sheet_contains_verbatim_context_answers_and_blank_checklists(self):
        sheet = review.render_sheet(self.workspace)
        self.assertIn('# grounded_strict_v2', sheet)
        self.assertIn('../prompts/grounded_strict_v2.json', sheet)
        self.assertIn('generation_strict_prompt_v2_human_review.json --finalized', sheet)
        self.assertEqual(sheet.count('## retrieval_'), 19)
        self.assertEqual(sheet.count('| correctness | |'), 19)
        for row in self.workspace['cases']:
            self.assertIn(review.fenced(row['generated_answer']), sheet)
            for chunk in row['retrieved_context_chunks']:
                self.assertIn(review.fenced(chunk['text']), sheet)

    def test_prepare_preserves_inputs_and_never_overwrites(self):
        paths = list(Path('evaluation/results').glob('*')) + list(Path('evaluation/prompts').glob('*.json')) + list(Path('app').rglob('*.py')) + [review.REFERENCE_PATH, review.RETRIEVAL_PATH]
        before = {p:file_hash(p) for p in paths if p.is_file()}
        with TemporaryDirectory() as directory:
            js, md = Path(directory)/'review.json', Path(directory)/'review.md'
            review.prepare(js, md, run_path=review.STRICT_V2_RUN_PATH)
            self.assertEqual(json.loads(js.read_text(encoding='utf-8')), self.workspace)
            with self.assertRaises(FileExistsError):
                review.prepare(js, md, run_path=review.STRICT_V2_RUN_PATH)
        self.assertEqual(before, {p:file_hash(p) for p in before})
