from copy import deepcopy
from pathlib import Path
import unittest
from pydantic import ValidationError
from evaluation.benchmark import EvidenceBenchmark, load_benchmark, validate_corpus


def example():
    return {"schema_version":2,"corpus":{"collection_name":"api-demo"},"cases":[{
        "question_id":"q","question":"question","category":"factual","answerable":True,
        "relevant_document_ids":["doc"],"relevant_chunks":[{"document_id":"doc","chunk_id":"a"}],
        "evidence_groups":[{"group_id":"g","requirement":"fact","acceptable_chunks":[
            {"document_id":"doc","chunk_id":"a"},{"document_id":"other","chunk_id":"b"}]}]}]}


class EvidenceBenchmarkTest(unittest.TestCase):
    def test_versions_and_legacy_unchanged(self):
        root=Path(__file__).resolve().parents[1]/"evaluation/benchmarks"
        v1=load_benchmark(root/"retrieval_v1.json")
        v2=load_benchmark(root/"retrieval_v2.json")
        self.assertEqual(len(v2.cases),19)
        for a,b in zip(v1.cases,v2.cases):
            self.assertEqual(a.model_dump(),b.model_dump(exclude={"evidence_groups"}))

    def test_shared_chunk_and_cross_document_alternatives(self):
        data=example()
        g=deepcopy(data["cases"][0]["evidence_groups"][0]); g["group_id"]="g2"
        data["cases"][0]["evidence_groups"].append(g)
        parsed=EvidenceBenchmark.model_validate(data)
        self.assertEqual(validate_corpus(parsed,{"chroma":{"a":"doc","b":"other"}}),[])
        self.assertTrue(validate_corpus(parsed,{"chroma":{"a":"doc"}}))
        self.assertTrue(validate_corpus(parsed,{"chroma":{"a":"doc","b":"wrong"}}))

    def test_invalid_groups(self):
        changes=[lambda c:c.pop("evidence_groups"),lambda c:c.update(evidence_groups=[]),
            lambda c:c["evidence_groups"][0].update(requirement=" "),
            lambda c:c["evidence_groups"][0].update(group_id=""),
            lambda c:c["evidence_groups"][0].update(acceptable_chunks=[]),
            lambda c:c["evidence_groups"].append(deepcopy(c["evidence_groups"][0])),
            lambda c:c["evidence_groups"][0]["acceptable_chunks"].append({"document_id":"doc","chunk_id":"a"}),
            lambda c:c["evidence_groups"][0]["acceptable_chunks"][0].update(document_id="wrong"),
            lambda c:c["relevant_chunks"][0].update(relevance=1),
            lambda c:c["evidence_groups"][0]["acceptable_chunks"][0].update(relevance=1)]
        for change in changes:
            data=example(); change(data["cases"][0])
            with self.subTest(change=change),self.assertRaises(ValidationError):
                EvidenceBenchmark.model_validate(data)

    def test_unanswerable_consistency(self):
        data=example(); c=data["cases"][0]
        c.update(answerable=False,relevant_document_ids=[],relevant_chunks=[])
        with self.assertRaises(ValidationError):
            EvidenceBenchmark.model_validate(data)
        c["evidence_groups"]=[]
        self.assertFalse(EvidenceBenchmark.model_validate(data).cases[0].answerable)
