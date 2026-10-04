"""Benchmark validation tests using synthetic inventories, without index access."""

from copy import deepcopy
from pathlib import Path
import unittest

from pydantic import ValidationError

from evaluation.benchmark import Benchmark, load_benchmark, validate_corpus


def case():
    return {
        "question_id": "q1",
        "question": "What is a transaction?",
        "category": "conceptual",
        "answerable": True,
        "relevant_document_ids": ["doc1"],
        "relevant_chunks": [{"chunk_id": "c1", "document_id": "doc1"}],
    }


def benchmark(*cases):
    return {"schema_version": 1, "corpus": {"collection_name": "api-demo"}, "cases": list(cases)}


class BenchmarkTest(unittest.TestCase):
    def test_committed_benchmark_is_valid(self):
        path = Path(__file__).resolve().parents[1] / "evaluation/benchmarks/retrieval_v1.json"
        loaded = load_benchmark(path)
        self.assertEqual(loaded.schema_version, 1)
        self.assertEqual(loaded.corpus.collection_name, "api-demo")
        self.assertTrue(all(chunk.relevance is None for case in loaded.cases for chunk in case.relevant_chunks))

    def test_empty_benchmark_remains_valid(self):
        self.assertEqual(Benchmark.model_validate(benchmark()).model_dump(), benchmark())

    def test_binary_case_and_multiple_documents(self):
        entry = case()
        entry["relevant_document_ids"].append("doc2")
        entry["relevant_chunks"].extend([
            {"chunk_id": "c2", "document_id": "doc1"},
            {"chunk_id": "c3", "document_id": "doc2"},
        ])
        parsed = Benchmark.model_validate(benchmark(entry))
        self.assertTrue(all(c.relevance is None for c in parsed.cases[0].relevant_chunks))
        self.assertEqual(validate_corpus(parsed, {"chroma": {"c1": "doc1", "c2": "doc1", "c3": "doc2"}}), [])

    def test_unanswerable_case(self):
        entry = case()
        entry.update(answerable=False, relevant_document_ids=[], relevant_chunks=[], notes="Not covered.")
        self.assertFalse(Benchmark.model_validate(benchmark(entry)).cases[0].answerable)

    def test_required_fields_types_and_unknown_fields(self):
        for field in case():
            entry = case()
            del entry[field]
            with self.subTest(missing=field), self.assertRaises(ValidationError):
                Benchmark.model_validate(benchmark(entry))
        for field, value in (("question_id", " "), ("question", ""), ("answerable", "true"), ("extra", "unexpected")):
            entry = case()
            entry[field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                Benchmark.model_validate(benchmark(entry))
        for version in (2, True, "1"):
            data = benchmark()
            data["schema_version"] = version
            with self.subTest(version=version), self.assertRaises(ValidationError):
                Benchmark.model_validate(data)
        for data in ({"schema_version": 1, "cases": []}, {"schema_version": 1, "corpus": {"collection_name": ""}, "cases": []}):
            with self.subTest(data=data), self.assertRaises(ValidationError):
                Benchmark.model_validate(data)

    def test_categories(self):
        for category in ("factual", "conceptual", "comparison", "multi_part", "out_of_scope"):
            entry = case()
            entry["category"] = category
            Benchmark.model_validate(benchmark(entry))
        entry["category"] = "single"
        with self.assertRaises(ValidationError):
            Benchmark.model_validate(benchmark(entry))

    def test_duplicate_question_ids(self):
        with self.assertRaises(ValidationError):
            Benchmark.model_validate(benchmark(case(), case()))

    def test_relevance_consistency(self):
        invalid = []
        entry = case()
        entry["relevant_chunks"] = []
        invalid.append(entry)
        entry = case()
        entry["answerable"] = False
        invalid.append(entry)
        entry = case()
        entry["relevant_document_ids"] = ["other"]
        invalid.append(entry)
        entry = case()
        entry["relevant_document_ids"].append("doc1")
        invalid.append(entry)
        entry = case()
        entry["relevant_chunks"].append(deepcopy(entry["relevant_chunks"][0]))
        invalid.append(entry)
        for entry in invalid:
            with self.subTest(entry=entry), self.assertRaises(ValidationError):
                Benchmark.model_validate(benchmark(entry))

    def test_optional_future_grades(self):
        for grade in (None, 1, 2):
            entry = case()
            entry["relevant_chunks"][0]["relevance"] = grade
            Benchmark.model_validate(benchmark(entry))
        for grade in (0, 3, True, "2", 1.5):
            entry = case()
            entry["relevant_chunks"][0]["relevance"] = grade
            with self.subTest(grade=grade), self.assertRaises(ValidationError):
                Benchmark.model_validate(benchmark(entry))

    def test_matching_inventories(self):
        parsed = Benchmark.model_validate(benchmark(case()))
        self.assertEqual(validate_corpus(parsed, {"chroma": {"c1": "doc1"}, "whoosh": {"c1": "doc1"}}), [])

    def test_missing_chunk_and_wrong_document(self):
        parsed = Benchmark.model_validate(benchmark(case()))
        issues = validate_corpus(parsed, {"chroma": {}, "whoosh": {"c1": "wrong"}})
        self.assertTrue(any("q1: chunk c1 missing from chroma" in issue for issue in issues))
        self.assertTrue(any("q1: chunk c1 belongs to wrong in whoosh, expected doc1" in issue for issue in issues))

    def test_full_corpus_mismatches_even_without_cases(self):
        parsed = Benchmark.model_validate(benchmark())
        inventories = {"chroma": {"shared": "doc1", "c1": "doc1"}, "whoosh": {"shared": "doc2", "c2": "doc2"}}
        original = deepcopy(inventories)
        issues = validate_corpus(parsed, inventories)
        self.assertEqual(len(issues), 3)
        self.assertTrue(any("chunk c1 present in chroma, missing from whoosh" in issue for issue in issues))
        self.assertTrue(any("chunk c2 present in whoosh, missing from chroma" in issue for issue in issues))
        self.assertTrue(any("chunk shared belongs to doc1 in chroma, but doc2 in whoosh" in issue for issue in issues))
        self.assertEqual(inventories, original)

    def test_inventory_required(self):
        with self.assertRaises(ValueError):
            validate_corpus(Benchmark.model_validate(benchmark()), {})


if __name__ == "__main__":
    unittest.main()
