"""Paired-pool orchestration checks; no corpus or embedding requests."""

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import Mock

from evaluation.benchmark import BenchmarkCase, Benchmark
from app.schemas.retrieval import RetrievedChunk
from evaluation.run_reranker_ablation import compare_case, run_ablation, aggregate


class RerankerAblationTest(unittest.TestCase):
    def case(self):
        return BenchmarkCase(
            question_id="q", question="specific evidence", category="factual",
            answerable=True, relevant_document_ids=["doc"],
            relevant_chunks=[{"chunk_id": "gold", "document_id": "doc"}],
        )

    def pool(self):
        return [RetrievedChunk(id=str(i), chunk_id="gold" if i == 0 else str(i),
                               document_id="doc", text="unrelated" if i == 0 else "specific evidence")
                for i in range(7)]

    def test_one_pool_per_query_and_full_pool_reranking(self):
        pool = self.pool()
        provider = Mock(return_value=pool)
        benchmark = Benchmark(schema_version=1, corpus={"collection_name": "api-demo"}, cases=[self.case()])
        with redirect_stdout(StringIO()):
            queries = run_ablation(benchmark, object(), pool_fn=provider)
        provider.assert_called_once()
        self.assertEqual(queries[0]["pool_ids"], [item.chunk_id for item in pool])
        self.assertEqual(queries[0]["canonical_ranks"][0]["before"], 1)
        self.assertEqual(queries[0]["canonical_ranks"][0]["after"], 7)
        self.assertEqual(queries[0]["rank_change"], "worsened")
        self.assertEqual(len(queries[0]["hybrid_reranked"]["retrieved_chunk_ids"]), 5)
        self.assertEqual(aggregate(queries)["final_k_rank_change"]["worsened"], 1)

    def test_existing_reranker_receives_exact_pool(self):
        from app.rag.reranker import rerank_items
        pool = self.pool()
        reranker = Mock(wraps=rerank_items)
        report = compare_case(self.case(), pool, rerank_fn=reranker)
        self.assertIs(reranker.call_args.args[1], pool)
        self.assertEqual(reranker.call_args.kwargs, {"k": 7})
        for row in report["heuristic_contributions"]:
            self.assertAlmostEqual(row["rerank_score"], row["overlap_count"] + row["phrase_bonus"] + row["rank_bonus"])

    def test_absent_canonical_and_empty_aggregate(self):
        report = compare_case(self.case(), [])
        self.assertEqual(report["rank_change"], "unchanged")
        self.assertEqual(report["hybrid"]["metrics"]["reciprocal_rank"], 0)
        self.assertIsNone(aggregate([])["hybrid"]["mrr"])


if __name__ == "__main__":
    unittest.main()
