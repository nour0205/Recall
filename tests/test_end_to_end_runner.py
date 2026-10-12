"""End-to-end runner logic; offline, no API key, indexes or model calls."""
import unittest

from app.seed_demo import load_manifest
from evaluation import run_end_to_end as e2e
from evaluation.generation_benchmark import load_generation_benchmark


class EndToEndRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark, cls.references = load_generation_benchmark()
        cls.notes = load_manifest()
        cls.chunk_map = e2e.benchmark_chunk_map(cls.notes)

    def case(self, question_id):
        index = [c.question_id for c in self.benchmark.cases].index(question_id)
        return self.benchmark.cases[index], self.references.cases[index]

    def row(self, question_id, answer, retrieved, calls=None, sources=None):
        case, reference = self.case(question_id)
        return e2e.build_row(
            case, reference, status_code=200,
            response={'answer': answer, 'route': 'concept_explanation', 'sources': sources or [], 'study_hint': None},
            plan={'route': 'concept_explanation', 'targets': []}, retrieved=retrieved,
            calls=calls or [], latency=1.0, chunk_map=self.chunk_map)

    def test_chunk_map_covers_every_demo_chunk(self):
        self.assertEqual(len(self.chunk_map), 27)
        self.assertEqual(self.chunk_map[('ml_gradient_descent', 0)], '4a373a64-f445-4926-964c-e32d4bef44e2')

    def test_expected_corpus_rebuilds_all_chunks(self):
        self.assertEqual(set(e2e.expected_corpus(self.notes)), set(self.chunk_map))

    def test_cited_labels_handles_single_grouped_and_repeated_citations(self):
        self.assertEqual(e2e.cited_labels('A [S1][S2]. B [S1, S3]. C [S2].'), [1, 2, 3])
        self.assertEqual(e2e.cited_labels("I don't know."), [])

    def test_refusal_outcomes(self):
        self.assertEqual(e2e.refusal_outcome('refuse', "I don't know."), 'correct_refusal')
        self.assertEqual(e2e.refusal_outcome('refuse', 'F1 is 2PR/(P+R) [S1].'), 'missed_refusal')
        self.assertEqual(e2e.refusal_outcome('answer', "I don't know."), 'false_refusal')
        self.assertEqual(e2e.refusal_outcome('answer', 'It may diverge [S1].'), 'answered')

    def test_retrieved_chunks_are_scored_against_benchmark_evidence_by_note_and_position(self):
        hit = [{'document_id': 'ml_gradient_descent', 'chunk_index': 0, 'text': '...'}]
        miss = [{'document_id': 'ml_cross_validation', 'chunk_index': 0, 'text': '...'}]
        self.assertTrue(self.row('retrieval_001', 'It may diverge [S1].', hit)['context_sufficient_for_full_answer'])
        self.assertFalse(self.row('retrieval_001', 'It may diverge [S1].', miss)['context_sufficient_for_full_answer'])

    def test_refusal_cases_have_no_evidence_requirement(self):
        row = self.row('retrieval_005', "I don't know.", [])
        self.assertIsNone(row['context_sufficient_for_full_answer'])
        self.assertEqual(row['refusal_outcome'], 'correct_refusal')

    def test_invalid_citations_and_fallback_are_flagged(self):
        sources = [{'document_id': 'ml_gradient_descent', 'chunk_index': 0, 'text': '...'}]
        calls = [{'kind': 'chat', 'stage': 'planner', 'usage': None}] + [{'kind': 'chat', 'stage': 'answer', 'usage': None}] * 2
        row = self.row('retrieval_001', 'It may diverge [S1][S4].', sources, calls=calls, sources=sources)
        self.assertEqual(row['invalid_cited_labels'], [4])
        self.assertTrue(row['fallback_suspected'])

    def test_fallback_detection_does_not_depend_on_the_planner(self):
        answer = {'kind': 'chat', 'stage': 'answer', 'usage': None}
        self.assertFalse(self.row('retrieval_001', 'x [S1].', [], calls=[answer])['fallback_suspected'])
        self.assertTrue(self.row('retrieval_001', 'x [S1].', [], calls=[answer, answer])['fallback_suspected'])

    def test_planner_bypass_matches_the_planner_contract(self):
        self.assertEqual(set(e2e.PLANNER_BYPASS), {'route', 'targets', 'reason'})
        self.assertEqual((e2e.PLANNER_BYPASS['route'], e2e.PLANNER_BYPASS['targets']), ('unknown', []))

    def test_summary_counts_behaviour_evidence_and_tokens(self):
        usage = {'prompt_tokens': 10, 'completion_tokens': 2, 'total_tokens': 12}
        calls = [{'kind': 'chat', 'stage': 'planner', 'usage': usage}, {'kind': 'chat', 'stage': 'answer', 'usage': usage},
                 {'kind': 'embedding', 'stage': 'query', 'usage': {'prompt_tokens': 5, 'total_tokens': 5}}]
        hit = [{'document_id': 'ml_gradient_descent', 'chunk_index': 0, 'text': '...'}]
        rows = [self.row('retrieval_001', 'It may diverge [S1].', hit, calls=calls, sources=hit),
                self.row('retrieval_002', "I don't know.", [], calls=calls),
                self.row('retrieval_005', "I don't know.", [], calls=calls)]
        summary = e2e.summarize(rows)
        self.assertEqual(summary['expected_refusals_refused'], '1/1')
        self.assertEqual(summary['answerable_falsely_refused'], '1/2')
        self.assertEqual(summary['answerable_with_all_required_evidence_retrieved'], '1/2')
        self.assertEqual(summary['answers_with_citations'], '1/1')
        self.assertEqual(summary['tokens']['planner']['total_tokens'], 36)
        self.assertEqual(summary['tokens']['query_embeddings']['calls'], 3)
        self.assertEqual(summary['latency_seconds']['median'], 1.0)


if __name__ == '__main__':
    unittest.main()
