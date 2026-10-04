import unittest
from unittest.mock import Mock
from app.schemas.retrieval import RetrievedChunk
from evaluation.semantic_reranker import SemanticReranker


class SemanticRerankerTest(unittest.TestCase):
    def pool(self):
        return [RetrievedChunk(id=str(i), chunk_id=str(i), document_id="doc", text=f"text {i}",
                               metadata={"nested": {"page": i}}, score=.2, bm25_score=3,
                               hybrid_score=.03, rank=i+1, found_by_vector=True,
                               found_by_bm25=True, retrieval_type="hybrid") for i in range(3)]

    def test_alignment_order_and_preservation(self):
        scorer = Mock()
        scorer.predict.return_value = [.1, .9, .5]
        pool = self.pool()
        ranked = SemanticReranker(scorer).rerank("question", pool, k=3)
        self.assertEqual([r.chunk_id for r in ranked], ["1", "2", "0"])
        scorer.predict.assert_called_once_with([( "question", c.text) for c in pool],
            batch_size=16, show_progress_bar=False, convert_to_numpy=True)
        for row in ranked:
            saved = row.model_dump()
            score = saved.pop("semantic_score")
            self.assertEqual(saved, pool[int(row.chunk_id)].model_dump())
            self.assertEqual(score, [.1, .9, .5][int(row.chunk_id)])
        self.assertFalse(hasattr(pool[0], "semantic_score"))

    def test_stable_ties_and_final_k(self):
        scorer = Mock()
        scorer.predict.return_value = [.7, .7, .9]
        result = SemanticReranker(scorer).rerank("q", self.pool(), k=2)
        self.assertEqual([r.chunk_id for r in result], ["2", "0"])
        self.assertEqual(len(scorer.predict.call_args.args[0]), 3)

    def test_empty_and_invalid_k(self):
        scorer = Mock()
        self.assertEqual(SemanticReranker(scorer).rerank("q", []), [])
        scorer.predict.assert_not_called()
        with self.assertRaises(ValueError):
            SemanticReranker(scorer).rerank("q", [], k=0)

    def test_bad_scores(self):
        for scores in ([1], [0, float("nan"), 1]):
            scorer = Mock()
            scorer.predict.return_value = scores
            with self.assertRaises(ValueError):
                SemanticReranker(scorer).rerank("q", self.pool())

    def test_full_union_scored_before_final_selection(self):
        from evaluation.benchmark import BenchmarkCase
        from evaluation.run_semantic_ablation import compare_semantic
        pool = [RetrievedChunk(id=str(i), chunk_id=str(i), document_id="doc",
            text="passage") for i in range(12)]
        case = BenchmarkCase(question_id="q", question="evidence", category="factual", answerable=True,
            relevant_document_ids=["doc"], relevant_chunks=[{"document_id": "doc", "chunk_id": "11"}])
        scorer = Mock()
        scorer.predict.return_value = list(range(12))
        scorer.tokenizer.return_value = {"input_ids": [[1] * (513 if i == 11 else 10) for i in range(12)]}
        result = compare_semantic(case, pool, SemanticReranker(scorer))
        semantic = result["hybrid_semantic_reranked"]
        self.assertEqual(len(scorer.predict.call_args.args[0]), 12)
        self.assertEqual(semantic["retrieved_chunk_ids"], ["11", "10", "9", "8", "7"])
        self.assertEqual(semantic["truncated_chunk_ids"], ["11"])
        self.assertEqual(semantic["earliest_canonical_rank"], 1)
        self.assertEqual(semantic["rank_change"], "improved")
