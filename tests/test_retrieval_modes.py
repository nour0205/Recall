"""Offline regression checks; embeddings are stubbed before application imports."""

from copy import deepcopy
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

# Avoid requiring an API key or constructing an OpenAI client during these tests.
embedder_stub = ModuleType("app.embeddings.embedder")
embedder_stub.embed_texts = Mock(return_value=[[0.1, 0.2]])
original_embedder = sys.modules.get("app.embeddings.embedder")
sys.modules["app.embeddings.embedder"] = embedder_stub
try:
    from app.rag import hybrid_retriever as shared
    from app.rag.reranker import rerank_items
    from app.schemas.retrieval import RetrievedChunk
    from evaluation.retrieval import retrieve
finally:
    if original_embedder is None:
        del sys.modules["app.embeddings.embedder"]
    else:
        sys.modules["app.embeddings.embedder"] = original_embedder


def row(chunk_id, text="unrelated passage", document_id="lecture"):
    return {
        "document": text,
        "metadata": {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "chunk_index": 0,
            "course": "databases",
            "owner": "student",
        },
        "distance": 0.25,
    }


def whoosh_row(chunk_id, text="unrelated passage", document_id="lecture"):
    result = row(chunk_id, text, document_id)
    result["text"] = result.pop("document")
    result["id"] = chunk_id
    result["score"] = 2.5
    return result


class RetrievalModesTest(unittest.TestCase):
    def setUp(self):
        self.store = Mock()
        self.embedding = patch.object(shared, "embed_texts", return_value=[[0.1, 0.2]]).start()
        self.whoosh = patch.object(shared, "search_whoosh", return_value=[]).start()
        self.addCleanup(patch.stopall)

    def test_vector_only_preserves_metadata_and_identity(self):
        self.store.query_with_scores.return_value = [row("v1"), row("v2")]
        results = retrieve(self.store, "question", mode="vector", k=1, candidate_k=2)
        self.store.query_with_scores.assert_called_once_with(
            query_embedding=[0.1, 0.2], k=2, where=None
        )
        self.whoosh.assert_not_called()
        self.assertEqual([item.id for item in results], ["v1"])
        self.assertEqual(results[0].chunk_id, "v1")
        self.assertEqual(results[0].metadata, row("v1")["metadata"])
        self.assertTrue(results[0].found_by_vector)
        self.assertFalse(results[0].found_by_bm25)

    def test_bm25_only_preserves_post_limit_filtering_and_ranks(self):
        self.whoosh.return_value = [whoosh_row("b1", document_id="other"), whoosh_row("b2")]
        results = retrieve(
            self.store, "question", mode="bm25", k=2,
            where={"document_id": "lecture"},
        )
        self.embedding.assert_not_called()
        self.store.query_with_scores.assert_not_called()
        self.whoosh.assert_called_once_with("question", limit=2)
        self.assertEqual([item.id for item in results], ["b2"])
        self.assertEqual(results[0].rank, 2)
        self.assertEqual(results[0].score, 2.5)
        self.assertTrue(results[0].found_by_bm25)
        self.assertEqual(results[0].metadata, whoosh_row("b2")["metadata"])

    def test_hybrid_modes_share_full_union_before_final_selection(self):
        vector = [row(f"v{i}") for i in range(10)]
        bm25 = [whoosh_row(f"b{i}") for i in range(10)]
        # A candidate below both final k and candidate_k in the fused ordering
        # must still be eligible for reranking.
        bm25[-1]["text"] = "exam revision priority exam revision priority"
        self.store.query_with_scores.side_effect = lambda **kwargs: deepcopy(vector)
        self.whoosh.side_effect = lambda *args, **kwargs: deepcopy(bm25)
        with patch("evaluation.retrieval.reciprocal_rank_fusion", wraps=shared.reciprocal_rank_fusion) as fusion:
            hybrid = retrieve(self.store, "exam revision priority", mode="hybrid", k=5, candidate_k=10)
            with patch("evaluation.retrieval.rerank_items", wraps=rerank_items) as rerank:
                ranked = retrieve(self.store, "exam revision priority", mode="hybrid_reranked", k=5, candidate_k=10)
        self.assertEqual(fusion.call_args_list[0], fusion.call_args_list[1])
        for call in self.store.query_with_scores.call_args_list:
            self.assertEqual(call.kwargs["k"], 10)
        for call in self.whoosh.call_args_list:
            self.assertEqual(call.kwargs["limit"], 10)
        candidates = rerank.call_args.args[1]
        self.assertEqual(len(candidates), 20)
        self.assertEqual([item.id for item in hybrid], [item.id for item in candidates[:5]])
        self.assertNotIn("b9", [item.id for item in candidates[:10]])
        self.assertEqual(ranked[0].id, "b9")
        self.assertEqual(ranked[0].metadata, bm25[-1]["metadata"])
        self.assertEqual(len(ranked), 5)

    def test_production_hybrid_retains_limits_rrf_and_filtering(self):
        self.store.query_with_scores.return_value = [row("shared"), row("vector")]
        self.whoosh.return_value = [
            whoosh_row("excluded", document_id="other"), whoosh_row("shared"),
        ]
        where = {"document_id": "lecture"}
        results = shared.hybrid_retrieve(self.store, "question", k=2, where=where)
        self.store.query_with_scores.assert_called_once_with(
            query_embedding=[0.1, 0.2], k=2, where=where
        )
        self.whoosh.assert_called_once_with("question", limit=2)
        self.assertEqual([item.id for item in results], ["shared", "vector"])
        self.assertAlmostEqual(results[0].hybrid_score, 1 / 61 + 1 / 62)
        self.assertEqual(results[0].retrieval_type, "hybrid")
        self.assertEqual(results[0].bm25_score, 2.5)
        self.assertTrue(results[0].found_by_vector)
        self.assertTrue(results[0].found_by_bm25)

    def test_empty_results_for_all_modes(self):
        self.store.query_with_scores.return_value = []
        for mode in ("vector", "bm25", "hybrid", "hybrid_reranked"):
            with self.subTest(mode=mode):
                self.assertEqual(retrieve(self.store, "question", mode=mode), [])

    def test_invalid_configuration_fails_before_search(self):
        for options in ({"mode": "invalid"}, {"k": 0}, {"k": 5, "candidate_k": 4}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                retrieve(self.store, "question", **options)
        self.embedding.assert_not_called()
        self.whoosh.assert_not_called()

    def test_legacy_identity_and_metadata_defaults(self):
        self.store.query_with_scores.return_value = [
            {"document": "legacy text", "metadata": {"document_id": "legacy", "chunk_index": 3}}
        ]
        result = retrieve(self.store, "question", k=1)[0]
        self.assertEqual(result.id, "legacy:3")
        self.assertIsNone(result.chunk_id)
        first = RetrievedChunk(id="a", document_id="doc", text="text")
        second = RetrievedChunk(id="b", document_id="doc", text="text")
        first.metadata["course"] = "math"
        self.assertEqual(second.metadata, {})


if __name__ == "__main__":
    unittest.main()
