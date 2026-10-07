"""Final four-way aggregates retain exact adjudication and frozen controls."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation import generation_prompt_comparison as comparison
from evaluation.generation_benchmark import file_hash


class FinalComparisonTests(unittest.TestCase):
    def test_exact_strict_v2_adjudication_and_expected_aggregates(self):
        report = comparison.build_comparison(sources=comparison.FINAL_SOURCES)
        result = report['experiments']['grounded_strict_v2']
        expected = {'correctness': (14, 16), 'groundedness': (18, 19),
                    'citation_correctness': (15, 16), 'refusal_correctness': (3, 3),
                    'prompt_compliance': (3, 3), 'full_completeness_rate': (13, 16)}
        for key, counts in expected.items():
            metric = result['metrics'][key]
            self.assertEqual((metric['passed_count'], metric['eligible_count']), counts)
        self.assertEqual(result['metrics']['mean_completeness']['score_sum'], 14.5)
        self.assertEqual(result['metrics']['mean_completeness']['eligible_count'], 16)
        self.assertEqual(result['unsupported_elaboration']['question_ids'], ['retrieval_013'])
        self.assertEqual(result['unsupported_elaboration']['eligible_count'], 19)
        self.assertEqual(result['failures']['failed_question_ids'], ['retrieval_008', 'retrieval_010', 'retrieval_012', 'retrieval_013'])
        review = json.loads(Path(result['review']['path']).read_text(encoding='utf-8'))
        row = next(r for r in review['cases'] if r['question_id']=='retrieval_013')
        self.assertEqual(row['unsupported_claims'], ['response adds the unsupported explanation that evaluating across multiple splits provides a more reliable estimate of generalization in the exact claim form used'])
        row = next(r for r in review['cases'] if r['question_id']=='retrieval_004')
        self.assertEqual(row['reviewer_notes'], 'Strict v1 false refusal fixed')

    def test_four_way_denominators_and_transitions_match_source_labels(self):
        report = comparison.build_comparison(sources=comparison.FINAL_SOURCES)
        self.assertEqual(list(report['experiments']), list(comparison.FINAL_SOURCES))
        for name, stem in comparison.FINAL_SOURCES.items():
            source = json.loads((comparison.RESULTS/(stem+'_human_review.json')).read_text(encoding='utf-8'))
            metrics = report['experiments'][name]['metrics']
            for key in ('correctness', 'groundedness', 'refusal_correctness', 'citation_correctness', 'prompt_compliance'):
                self.assertEqual(metrics[key]['eligible_count'], sum(type(r[key]) is int for r in source['cases']))
            for transition in report['case_transitions']:
                original = next(r for r in source['cases'] if r['question_id']==transition['question_id'])
                for key, value in transition['experiments'][name].items():
                    self.assertEqual(value, original[key])

    def test_final_report_write_is_deterministic_preserves_history_and_has_all_columns(self):
        paths = list(comparison.RESULTS.glob('*.json')) + list(Path('app').rglob('*.py'))
        before = {p:file_hash(p) for p in paths}
        with TemporaryDirectory() as directory:
            js, md = Path(directory)/'final.json', Path(directory)/'final.md'
            report = comparison.write_comparison(js, md, final=True)
            self.assertEqual(report, comparison.build_comparison(sources=comparison.FINAL_SOURCES))
            self.assertEqual(json.loads(js.read_text(encoding='utf-8')), report)
            sheet = md.read_text(encoding='utf-8')
            self.assertIn('| Dimension | Baseline | Strict v1 | Balanced v2 | Strict v2 |', sheet)
            self.assertIn('1/19', sheet)
            self.assertIn('generation_prompt_ablation_comparison_final.json', sheet)
            self.assertIn('no statistical significance', sheet)
            self.assertEqual(sheet.count('| retrieval_'), 9)
            with self.assertRaises(FileExistsError):
                comparison.write_comparison(js, md, final=True)
        self.assertEqual(before, {p:file_hash(p) for p in paths})

    def test_readme_example_is_verbatim_and_table_matches_verified_results(self):
        readme = Path('README.md').read_text(encoding='utf-8')
        question = 'What happens if the learning rate is too large during gradient descent?'
        for stem, excerpt in (
            ('generation_baseline_v1', 'A **learning rate** that is too large results in overshooting the optimal parameter values, leading to instability in the training process [S1].'),
            ('generation_strict_prompt_v1', 'A learning rate that is too large may cause divergence [S1].')):
            raw = json.loads((comparison.RESULTS/(stem+'.json')).read_text(encoding='utf-8'))
            row = next(r for r in raw['queries'] if r['question_id']=='retrieval_001')
            self.assertEqual(row['question'], question)
            self.assertIn(excerpt, row['generated_answer'])
            self.assertIn(excerpt, readme)
        report = comparison.build_comparison(sources=comparison.FINAL_SOURCES)
        for name, label in (('generation_baseline_v1','Baseline'), ('grounded_strict_v1','Strict v1'), ('grounded_balanced_v2','Balanced v2'), ('grounded_strict_v2','Strict v2')):
            result = report['experiments'][name]
            row = next(line for line in readme.splitlines() if line.startswith('| '+label+' |'))
            for key in ('groundedness','citation_correctness'):
                m = result['metrics'][key]
                self.assertIn(f"{m['passed_count']}/{m['eligible_count']}",row)
            m = result['metrics']['mean_completeness']
            self.assertIn(f"{m['score_sum']:g}/{m['eligible_count']}",row)
