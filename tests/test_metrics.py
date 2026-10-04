"""Hand-calculated metric checks without application or corpus dependencies."""

import unittest

from evaluation.metrics import hit_at_k, recall_at_k, reciprocal_rank


class MetricsTest(unittest.TestCase):
    def test_relevant_at_rank_one(self):
        self.assertEqual(hit_at_k(["a", "b"], ["a"], 1), 1.0)
        self.assertEqual(recall_at_k(["a", "b"], ["a"], 1), 1.0)
        self.assertEqual(reciprocal_rank(["a", "b"], ["a"]), 1.0)

    def test_relevant_at_rank_three_and_cutoff(self):
        retrieved = ["x", "y", "a"]
        self.assertEqual(hit_at_k(retrieved, ["a"], 2), 0.0)
        self.assertEqual(recall_at_k(retrieved, ["a"], 2), 0.0)
        self.assertEqual(hit_at_k(retrieved, ["a"], 3), 1.0)
        self.assertEqual(recall_at_k(retrieved, ["a"], 3), 1.0)
        self.assertAlmostEqual(reciprocal_rank(retrieved, ["a"]), 1 / 3)

    def test_no_relevant_result(self):
        self.assertEqual(hit_at_k(["x", "y"], ["a"], 2), 0.0)
        self.assertEqual(recall_at_k(["x", "y"], ["a"], 2), 0.0)
        self.assertEqual(reciprocal_rank(["x", "y"], ["a"]), 0.0)

    def test_partial_recall_and_first_relevant_rank(self):
        retrieved = ["x", "b", "a", "c"]
        relevant = ["a", "b", "c", "d"]
        self.assertEqual(hit_at_k(retrieved, relevant, 3), 1.0)
        self.assertEqual(recall_at_k(retrieved, relevant, 3), 2 / 4)
        self.assertEqual(reciprocal_rank(retrieved, relevant), 0.5)

    def test_all_relevant_and_k_larger_than_results(self):
        retrieved = ["b", "x", "a"]
        self.assertEqual(hit_at_k(retrieved, ["a", "b"], 10), 1.0)
        self.assertEqual(recall_at_k(retrieved, ["a", "b"], 10), 1.0)

    def test_duplicate_retrieved_and_relevant_ids(self):
        retrieved = ["a", "a", "b"]
        relevant = ["a", "a", "b"]
        self.assertEqual(hit_at_k(retrieved, relevant, 2), 1.0)
        self.assertEqual(recall_at_k(retrieved, relevant, 2), 0.5)
        self.assertEqual(recall_at_k(retrieved, relevant, 3), 1.0)
        self.assertEqual(reciprocal_rank(retrieved, relevant), 1.0)

    def test_duplicates_preserve_original_positions(self):
        retrieved = ["x", "x", "a"]
        self.assertEqual(hit_at_k(retrieved, ["a"], 2), 0.0)
        self.assertEqual(recall_at_k(retrieved, ["a"], 2), 0.0)
        self.assertAlmostEqual(reciprocal_rank(retrieved, ["a"]), 1 / 3)

    def test_empty_results(self):
        self.assertEqual(hit_at_k([], ["a"], 3), 0.0)
        self.assertEqual(recall_at_k([], ["a"], 3), 0.0)
        self.assertEqual(reciprocal_rank([], ["a"]), 0.0)

    def test_no_relevant_chunks(self):
        for retrieved in ([], ["a", "b"]):
            with self.subTest(retrieved=retrieved):
                self.assertEqual(hit_at_k(retrieved, [], 3), 0.0)
                self.assertIsNone(recall_at_k(retrieved, [], 3))
                self.assertEqual(reciprocal_rank(retrieved, []), 0.0)

    def test_invalid_k_even_with_empty_relevance(self):
        for function in (hit_at_k, recall_at_k):
            for k in (0, -1, True, False, 1.5, "3", None):
                with self.subTest(function=function.__name__, k=k), self.assertRaises(ValueError):
                    function([], [], k)

    def test_iterable_relevance_and_unchanged_inputs(self):
        retrieved = ["x", "a", "a"]
        relevant = ["a", "b", "a"]
        self.assertEqual(hit_at_k(tuple(retrieved), iter(relevant), 3), 1.0)
        self.assertEqual(recall_at_k(retrieved, iter(relevant), 3), 0.5)
        self.assertEqual(reciprocal_rank(retrieved, iter(relevant)), 0.5)
        self.assertEqual(retrieved, ["x", "a", "a"])
        self.assertEqual(relevant, ["a", "b", "a"])


if __name__ == "__main__":
    unittest.main()
