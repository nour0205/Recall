"""LLM judge plumbing and agreement metrics; offline, no model calls."""
import json
import unittest

from evaluation import judge as judge_lib
from evaluation import run_judge
from evaluation.judge_agreement import cohens_kappa, compare, disagreements


class JudgeInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = run_judge.calibration_cases()

    def test_calibration_set_is_four_finalized_runs_of_nineteen(self):
        self.assertEqual(len(self.cases), 76)
        self.assertEqual({c['run'] for c in self.cases}, set(run_judge.HUMAN_REVIEWS))

    def test_judge_never_sees_human_labels_or_reviewer_notes(self):
        for case in self.cases:
            rendered = judge_lib.render_input(case)
            visible = json.dumps(judge_lib.judge_input(case))
            self.assertNotIn('"human"', visible)
            self.assertNotIn('reviewer_notes', visible)
            for label in ('completeness_points', 'missing_required_points', 'unsupported_claims'):
                self.assertNotIn(label, rendered)

    def test_sources_keep_prompt_order_and_refuse_cases_have_no_points(self):
        case = next(c for c in self.cases if c['question_id'] == 'retrieval_005')
        data = judge_lib.judge_input(case)
        self.assertEqual([s['label'] for s in data['sources']], [f'[S{i}]' for i in range(1, len(case['sources']) + 1)])
        self.assertEqual(data['required_points'], [])

    def test_prompt_embeds_the_human_rubric(self):
        prompt = judge_lib.load_prompt()
        self.assertNotIn('{rubric}', prompt['instructions'])
        self.assertIn('Valid citation syntax alone is insufficient', prompt['instructions'])

    def test_v2_adds_conventions_before_the_rubric(self):
        prompt = judge_lib.load_prompt(run_judge.DEFAULT_PROMPT)
        self.assertEqual(prompt['prompt_id'], 'judge_v2')
        conventions = prompt['instructions'].index('C4. Qualifiers')
        self.assertLess(conventions, prompt['instructions'].index('Rubric:'))

    def test_end_to_end_cases_use_the_context_the_answer_saw(self):
        cases = run_judge.end_to_end_cases(run_judge.RESULTS / 'end_to_end_v1_20261012T071846Z.json')
        self.assertEqual(len(cases), 19)
        self.assertTrue(all(len(c['sources']) == 5 for c in cases))


class JudgmentValidationTests(unittest.TestCase):
    def setUp(self):
        self.case = {'expected_behavior': 'answer', 'answer': 'It may diverge [S1].',
                     'required_points': [{'point_id': 'a'}, {'point_id': 'b'}]}

    def judgment(self, points):
        return {'point_judgments': [{'point_id': p, 'judgment': j, 'reason': ''} for p, j in points],
                'groundedness': 1, 'refusal_correctness': 1}

    def test_valid_judgment_and_completeness(self):
        j = self.judgment([('a', 'pass'), ('b', 'fail')])
        self.assertEqual(judge_lib.validate_judgment(j, self.case), [])
        self.assertEqual(judge_lib.completeness_score(j, self.case), 0.5)

    def test_refusal_correctness_na_follows_the_human_convention(self):
        j = self.judgment([('a', 'pass'), ('b', 'pass')])
        j['refusal_correctness'] = 'N/A'
        self.assertEqual(judge_lib.validate_judgment(j, self.case), [])
        refused = {**self.case, 'answer': "I don't know."}
        self.assertTrue(judge_lib.validate_judgment(j, refused))

    def test_missing_or_reordered_points_are_rejected(self):
        self.assertTrue(judge_lib.validate_judgment(self.judgment([('b', 'pass'), ('a', 'pass')]), self.case))
        self.assertTrue(judge_lib.validate_judgment(self.judgment([('a', 'pass')]), self.case))


class AgreementTests(unittest.TestCase):
    def test_kappa_known_values(self):
        self.assertEqual(cohens_kappa([(1, 1), (0, 0)]), 1.0)
        self.assertAlmostEqual(cohens_kappa([(1, 1), (1, 0), (0, 1), (0, 0)]), 0.0)
        # Judge always says 1 while humans vary: high raw agreement, zero kappa.
        self.assertAlmostEqual(cohens_kappa([(1, 1)] * 9 + [(0, 1)]), 0.0)
        self.assertIsNone(cohens_kappa([(1, 1)] * 3))

    def test_compare_and_disagreements(self):
        def case(run, h, j, hp, jp, score, jscore):
            return {'run': run, 'question_id': 'q', 'expected_behavior': 'answer',
                    'human': {'groundedness': h, 'correctness': 1, 'citation_correctness': 1, 'refusal_correctness': 1,
                              'completeness_points': [{'point_id': 'p', 'judgment': hp}], 'completeness_score': score},
                    'judge': {'groundedness': j, 'correctness': 1, 'citation_correctness': 1, 'refusal_correctness': 1,
                              'point_judgments': [{'point_id': 'p', 'judgment': jp, 'reason': 'r'}]},
                    'judge_completeness_score': jscore}
        cases = [case('a', 1, 1, 'pass', 'pass', 1.0, 1.0), case('b', 0, 1, 'fail', 'pass', 0.0, 1.0)]
        report = compare(cases)
        self.assertEqual(report['groundedness']['agreement'], '1/2')
        self.assertEqual(report['groundedness']['confusion'], {'human=0 judge=1': 1, 'human=1 judge=1': 1})
        self.assertEqual(report['completeness_points']['agreement'], '1/2')
        self.assertEqual(report['completeness_score_mean_abs_error'], 0.5)
        self.assertEqual([d['dimension'] for d in disagreements(cases)], ['groundedness', 'point:p'])


if __name__ == '__main__':
    unittest.main()
