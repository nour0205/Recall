"""Scoped keyword search on a real in-memory Whoosh index; offline."""

import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

from whoosh.filedb.filestore import RamStorage

# Imported first: patch.dict below drops modules first imported inside it.
from app.vectordb import whoosh_index

# hybrid_retriever imports the embedder; keyword search never calls it.
embedder_stub = ModuleType("app.embeddings.embedder")
embedder_stub.embed_texts = Mock()
with patch.dict(sys.modules, {"app.embeddings.embedder": embedder_stub}):
    from app.rag import hybrid_retriever


class ScopedKeywordSearchTest(unittest.TestCase):
    def setUp(self):
        self.ix = RamStorage().create_index(whoosh_index.get_schema())
        writer = self.ix.writer()
        # Twelve chunks of another note match "learning rate" more strongly
        # than the single chunk of the note the question is scoped to.
        for i in range(12):
            writer.add_document(document_id="other", chunk_id=f"o{i}", chunk_index=i, source="", owner="",
                                content="Learning rate, learning rate: the learning rate sets the step size.")
        writer.add_document(document_id="target", chunk_id="t0", chunk_index=0, source="", owner="",
                            content="Gradient descent uses a learning rate.")
        writer.commit()
        self.addCleanup(self.ix.close)
        patch.object(whoosh_index, "get_or_create_index", return_value=self.ix).start()
        self.addCleanup(patch.stopall)

    def test_scope_is_applied_before_the_top_k_cut(self):
        results = hybrid_retriever.retrieve_bm25_candidates(
            "What does the learning rate do?", k=10, where={"document_id": "target"})
        self.assertEqual([r["chunk_id"] for r in results], ["t0"])

    def test_ranks_count_only_in_scope_results(self):
        results = hybrid_retriever.retrieve_bm25_candidates(
            "learning rate", k=10, where={"document_id": "target"})
        self.assertEqual(results[0]["rank"], 1)

    def test_unscoped_search_still_returns_the_global_top_k(self):
        results = hybrid_retriever.retrieve_bm25_candidates("learning rate", k=10)
        self.assertEqual(len(results), 10)
        self.assertEqual([r["rank"] for r in results], list(range(1, 11)))
        self.assertNotIn("t0", [r["chunk_id"] for r in results])


if __name__ == "__main__":
    unittest.main()
