"""Runner orchestration and aggregation checks with deterministic fake retrieval."""

from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from evaluation.benchmark import Benchmark
from evaluation.run_retrieval_benchmark import MODES, aggregate_results, run_cases


class RetrievalRunnerTest(unittest.TestCase):
    def benchmark(self):
        return Benchmark.model_validate({
            "schema_version": 1,
            "corpus": {"collection_name": "api-demo"},
            "cases": [
                {"question_id": "positive", "question": "Known?", "category": "factual",
                 "answerable": True, "relevant_document_ids": ["doc"],
                 "relevant_chunks": [{"chunk_id": "gold", "document_id": "doc"}]},
                {"question_id": "negative", "question": "Unknown?", "category": "out_of_scope",
                 "answerable": False, "relevant_document_ids": [], "relevant_chunks": []},
            ],
        })

    def test_modes_depths_order_latency_and_negative_exclusion(self):
        retrieve = Mock(return_value=[SimpleNamespace(chunk_id="other"), SimpleNamespace(chunk_id="gold")])
        store = object()
        clock = [value for i in range(8) for value in (i * 2.0, i * 2.0 + 0.25)]
        with patch("evaluation.run_retrieval_benchmark.time.perf_counter", side_effect=clock), redirect_stdout(StringIO()):
            queries = run_cases(self.benchmark(), store, retrieve_fn=retrieve)
        self.assertEqual(retrieve.call_count, 8)
        for i, call in enumerate(retrieve.call_args_list):
            self.assertIs(call.args[0], store)
            self.assertEqual(call.kwargs, {"mode": MODES[i % 4], "k": 5, "candidate_k": 10})
        for query in queries:
            for result in query["results"].values():
                self.assertEqual(result["retrieved_chunk_ids"], ["other", "gold"])
                self.assertEqual(result["latency_seconds"], 0.25)
        self.assertIsNone(queries[1]["results"]["vector"]["metrics"]["recall_at_5"])
        for result in aggregate_results(queries).values():
            self.assertEqual(result["quality_query_count"], 1)
            self.assertEqual(result["latency_query_count"], 2)
            self.assertEqual(result["metrics"]["hit_at_1"], 0.0)
            self.assertEqual(result["metrics"]["hit_at_3"], 1.0)
            self.assertEqual(result["metrics"]["recall_at_5"], 1.0)
            self.assertEqual(result["metrics"]["mrr"], 0.5)
            self.assertEqual(result["mean_latency_seconds"], 0.25)

    def test_empty_aggregates_are_undefined(self):
        for result in aggregate_results([]).values():
            self.assertEqual(result["quality_query_count"], 0)
            self.assertTrue(all(value is None for value in result["metrics"].values()))
            self.assertIsNone(result["mean_latency_seconds"])

    def test_missing_chunk_identity_fails(self):
        with redirect_stdout(StringIO()), self.assertRaises(ValueError):
            run_cases(self.benchmark(), object(), retrieve_fn=Mock(return_value=[SimpleNamespace(chunk_id=None)]))


if __name__ == "__main__":
    unittest.main()
