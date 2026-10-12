"""Notes library on real Chroma and Whoosh indexes; offline, fake embeddings."""
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import uuid

os.environ.setdefault("OPENAI_API_KEY", "test-placeholder")

import chromadb

from app import library
from app.schemas.api import IngestRequest
from app.vectordb import whoosh_index
from app.vectordb.chroma_store import ChromaStore

TEXT = ("Gradient descent minimizes a loss function. The learning rate controls the size of updates. "
        "A learning rate that is too large may cause divergence. ") * 6


def fake_embed(chunks):
    return [[float(len(chunk)), 1.0, 0.5] for chunk in chunks]


def request(document_id="gd", text=TEXT, **extra):
    return IngestRequest(document_id=document_id, text=text, document_type="lecture_note", **extra)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="recall-library-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        index_dir = patch.object(whoosh_index, "INDEX_DIR", self.tmp / "whoosh")
        index_dir.start()
        self.addCleanup(index_dir.stop)
        self.store = ChromaStore.__new__(ChromaStore)
        self.store.client = chromadb.EphemeralClient()
        self.store.collection = self.store.client.create_collection(f"test-{uuid.uuid4().hex}")

    def bm25_ids(self, document_id=None):
        return {r["chunk_id"] for r in whoosh_index.whoosh_records()
                if document_id is None or r["document_id"] == document_id}

    def vector_ids(self, document_id=None):
        where = {"document_id": document_id} if document_id else None
        return set(self.store.collection.get(where=where)["ids"])

    def test_ingest_writes_the_same_chunks_to_both_indexes(self):
        result = library.add_document(self.store, request(source="course", owner="me"), embed=fake_embed)
        self.assertEqual(result["status"], "ingested")
        self.assertGreater(result["chunks_added"], 1)
        self.assertEqual(self.vector_ids(), self.bm25_ids())
        self.assertTrue(library.check_consistency(self.store)["consistent"])
        record = whoosh_index.whoosh_records()[0]
        self.assertEqual((record["source"], record["owner"]), ("course", "me"))

    def test_notes_without_optional_metadata_can_be_added(self):
        # Chroma rejects None metadata values; a note with no course used to fail.
        bare = IngestRequest(document_id="bare", text=TEXT)
        self.assertEqual(library.add_document(self.store, bare, embed=fake_embed)["status"], "ingested")
        meta = self.store.collection.get(where={"document_id": "bare"}, include=["metadatas"])["metadatas"][0]
        self.assertNotIn("course", meta)

    def test_embedding_failure_writes_nothing(self):
        def broken(chunks):
            raise RuntimeError("embedding API down")
        with self.assertRaises(RuntimeError):
            library.add_document(self.store, request(), embed=broken)
        self.assertEqual((self.vector_ids(), self.bm25_ids()), (set(), set()))

    def test_keyword_index_failure_rolls_back_the_vector_index(self):
        with patch.object(library, "add_chunks_to_whoosh", side_effect=OSError("disk full")):
            with self.assertRaises(library.IngestionError):
                library.add_document(self.store, request(), embed=fake_embed)
        self.assertEqual((self.vector_ids(), self.bm25_ids()), (set(), set()))
        # The name is free again: a retry succeeds.
        self.assertEqual(library.add_document(self.store, request(), embed=fake_embed)["status"], "ingested")

    def test_vector_index_failure_writes_nothing_to_the_keyword_index(self):
        with patch.object(self.store, "add_texts", side_effect=ValueError("bad metadata")):
            with self.assertRaises(library.IngestionError):
                library.add_document(self.store, request(), embed=fake_embed)
        self.assertEqual((self.vector_ids(), self.bm25_ids()), (set(), set()))

    def test_duplicate_text_and_name_conflicts(self):
        library.add_document(self.store, request(), embed=fake_embed)
        self.assertEqual(library.add_document(self.store, request("other"), embed=fake_embed)["status"], "duplicate")
        self.assertEqual(library.add_document(self.store, request(text="Different notes."), embed=fake_embed)["status"], "conflict")

    def test_a_name_left_only_in_the_keyword_index_is_a_conflict(self):
        whoosh_index.add_chunks_to_whoosh([{"chunk_id": "orphan", "document_id": "gd", "chunk_index": 0, "text": "Old."}])
        self.assertEqual(library.add_document(self.store, request(), embed=fake_embed)["status"], "conflict")

    def test_delete_removes_a_note_from_both_indexes_only(self):
        library.add_document(self.store, request(), embed=fake_embed)
        library.add_document(self.store, request("keep", text="Threads share memory. Processes do not."), embed=fake_embed)
        kept = self.vector_ids("keep")
        result = library.delete_document(self.store, "gd")
        self.assertGreater(result["vector_chunks_deleted"], 0)
        self.assertEqual(result["vector_chunks_deleted"], result["bm25_chunks_deleted"])
        self.assertEqual((self.vector_ids("gd"), self.bm25_ids("gd")), (set(), set()))
        self.assertEqual((self.vector_ids(), self.bm25_ids()), (kept, kept))

    def test_delete_unknown_note_deletes_nothing(self):
        self.assertEqual(library.delete_document(self.store, "missing"),
                         {"vector_chunks_deleted": 0, "bm25_chunks_deleted": 0})

    def test_check_and_repair_fix_drift_without_embeddings(self):
        library.add_document(self.store, request(source="course"), embed=fake_embed)
        lost = sorted(self.vector_ids())[0]
        whoosh_index.delete_chunks_from_whoosh([lost])
        whoosh_index.add_chunks_to_whoosh([{"chunk_id": "orphan", "document_id": "ghost", "chunk_index": 0, "text": "Ghost."}])
        report = library.check_consistency(self.store)
        self.assertFalse(report["consistent"])
        self.assertEqual([r["chunk_id"] for r in report["vector_only"]], [lost])
        self.assertEqual(report["bm25_only"], [{"chunk_id": "orphan", "document_id": "ghost"}])
        self.assertEqual(library.repair(self.store), {"bm25_orphans_removed": 1, "bm25_chunks_restored": 1})
        self.assertTrue(library.check_consistency(self.store)["consistent"])
        restored = next(r for r in whoosh_index.whoosh_records() if r["chunk_id"] == lost)
        self.assertEqual(restored["source"], "course")


if __name__ == "__main__":
    unittest.main()
