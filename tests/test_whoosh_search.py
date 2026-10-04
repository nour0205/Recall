"""Natural-language query checks against an isolated in-memory Whoosh index."""

import unittest
from unittest.mock import patch

from whoosh.filedb.filestore import RamStorage

from app.vectordb.whoosh_index import get_schema, search_whoosh


class WhooshSearchTest(unittest.TestCase):
    def setUp(self):
        self.ix = RamStorage().create_index(get_schema())
        writer = self.ix.writer()
        fixtures = [
            ("gradient", "g1", "Gradient descent learning rate learning rate divergence."),
            ("accuracy", "a1", "Accuracy is misleading on imbalanced datasets."),
            ("process", "p1", "Processes have separate memory. Threads share memory for communication."),
            ("scheduling", "s1", "Aging raises priority to prevent starvation in CPU scheduling."),
            ("partial", "l1", "Learning useful concepts through practical examples today."),
            ("metadata", "m1", "Unrelated text has several words for testing source metadata."),
        ]
        for document_id, chunk_id, content in fixtures:
            writer.add_document(
                document_id=document_id, chunk_id=chunk_id, chunk_index=0,
                content=content, source="lecture" if chunk_id == "m1" else "", owner="student",
            )
        writer.commit()
        self.addCleanup(self.ix.close)
        self.mock_index = patch("app.vectordb.whoosh_index.get_or_create_index", return_value=self.ix).start()
        self.addCleanup(patch.stopall)

    def ids(self, query):
        return [row["chunk_id"] for row in search_whoosh(query, limit=10)]

    def test_full_questions_with_punctuation(self):
        self.assertEqual(self.ids("When can accuracy be a misleading evaluation metric?"), ["a1"])
        self.assertEqual(self.ids("How does aging help prevent starvation in CPU scheduling?"), ["s1"])
        self.assertEqual(self.ids("accuracy?!"), ["a1"])

    def test_stopwords_do_not_become_id_constraints(self):
        self.assertEqual(self.ids("the accuracy can be misleading"), self.ids("accuracy misleading"))

    def test_multiword_queries_use_partial_matches_and_rank(self):
        self.assertEqual(self.ids("learning rate"), ["g1", "l1"])
        self.assertEqual(self.ids("gradient descent"), ["g1"])
        self.assertEqual(self.ids("How do processes and threads differ in memory sharing and communication?"), ["p1"])

    def test_single_term(self):
        self.assertEqual(self.ids("aging"), ["s1"])

    def test_empty_and_stopword_only(self):
        for query in ("", "   ", "?!", "the and if in can be"):
            with self.subTest(query=query):
                self.assertEqual(self.ids(query), [])

    def test_query_language_is_literal_text(self):
        # No wildcard expansion or field restriction. Content analyzer removes OR.
        self.assertEqual(self.ids("aging* OR accuracy?"), self.ids("aging accuracy"))
        self.assertEqual(self.ids("source:accuracy"), self.ids("source accuracy"))
        self.assertIn("a1", self.ids("source:accuracy"))

    def test_metadata_fields_remain_searchable(self):
        self.assertEqual(self.ids("lecture"), ["m1"])
        self.assertEqual(self.ids("metadata"), ["m1"])

    def test_return_shape_scores_ranks_and_duplicate_query_terms(self):
        rows = search_whoosh("learning rate", limit=10)
        repeated = search_whoosh("learning learning rate", limit=10)
        self.assertEqual(rows, repeated)
        for rank, row in enumerate(rows, 1):
            self.assertEqual(row["rank"], rank)
            self.assertEqual(row["retrieval_type"], "bm25")
            self.assertEqual(row["id"], row["chunk_id"])
            self.assertEqual(row["metadata"]["chunk_id"], row["chunk_id"])
            self.assertEqual(row["metadata"]["owner"], "student")
            self.assertIsInstance(row["score"], float)
            self.assertGreater(row["score"], 0)
            self.assertIn("text", row)
            self.assertIn("document_id", row["metadata"])
            self.assertEqual(row["metadata"]["chunk_index"], 0)
        self.assertGreater(rows[0]["score"], rows[1]["score"])
        self.assertEqual(len(search_whoosh("learning rate", limit=1)), 1)


if __name__ == "__main__":
    unittest.main()
