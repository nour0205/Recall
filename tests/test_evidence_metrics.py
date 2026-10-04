import unittest
from evaluation.evidence_metrics import evidence_hit_at_k as hit, evidence_recall_at_k as recall, evidence_reciprocal_rank as rr


class EvidenceMetricsTest(unittest.TestCase):
    def test_alternatives(self):
        groups = [{"a", "b"}]
        self.assertEqual(hit(["x", "b"], groups, 1), 0)
        self.assertEqual(recall(["x", "b", "a"], groups, 3), 1)
        self.assertEqual(rr(["x", "b"], groups), .5)

    def test_independent_groups_and_duplicates(self):
        groups = [{"a", "b"}, {"c", "d"}]
        self.assertEqual(recall(["a", "a", "b", "d"], groups, 3), .5)
        self.assertEqual(recall(["a", "a", "b", "d"], groups, 4), 1)
        self.assertEqual(rr(["x", "x", "d"], groups), 1/3)

    def test_one_chunk_many_groups(self):
        groups = [{"a", "both"}, {"b", "both"}]
        self.assertEqual(recall(["both"], groups, 1), 1)
        self.assertEqual(hit(["both"], groups, 1), 1)

    def test_empty_and_no_hit(self):
        self.assertEqual(hit([], [{"a"}], 1), 0)
        self.assertEqual(recall(["x"], [{"a"}], 1), 0)
        self.assertEqual(rr(["x"], [{"a"}]), 0)
        self.assertEqual(hit(["x"], [], 1), 0)
        self.assertIsNone(recall(["x"], [], 1))
        self.assertEqual(rr(["x"], []), 0)

    def test_invalid_k_and_empty_group(self):
        for k in (0, -1, True, 1.5):
            for fn in (hit, recall):
                with self.assertRaises(ValueError):
                    fn([], [], k)
        with self.assertRaises(ValueError):
            rr([], [set()])
