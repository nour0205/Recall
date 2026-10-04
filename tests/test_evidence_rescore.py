import unittest
from copy import deepcopy
from evaluation.benchmark import EvidenceBenchmark
from evaluation.rescore_evidence import rescore, MODES
from evaluation.metrics import hit_at_k, recall_at_k, reciprocal_rank


class EvidenceRescoreTest(unittest.TestCase):
    def fixture(self):
        benchmark=EvidenceBenchmark.model_validate({"schema_version":2,"corpus":{"collection_name":"api-demo"},
            "cases":[{"question_id":"q","question":"question","category":"factual","answerable":True,
                "relevant_document_ids":["doc"],"relevant_chunks":[{"document_id":"doc","chunk_id":"canonical"}],
                "evidence_groups":[{"group_id":"g","requirement":"fact","acceptable_chunks":[
                    {"document_id":"doc","chunk_id":"canonical"},{"document_id":"doc","chunk_id":"alternative"}]}]},
                {"question_id":"negative","question":"unsupported","category":"out_of_scope","answerable":False,
                    "relevant_document_ids":[],"relevant_chunks":[],"evidence_groups":[]}]})
        saved={"configuration":{"candidate_k":10,"k":5},"queries":[]}
        for case in benchmark.cases:
            ids=["alternative"]
            gold=[c.chunk_id for c in case.relevant_chunks]
            canonical={f"{name}_at_{k}": fn(ids,gold,k) for name,fn in (("hit",hit_at_k),("recall",recall_at_k)) for k in (1,3,5)}
            canonical["reciprocal_rank"]=reciprocal_rank(ids,gold)
            saved["queries"].append(dict(question_id=case.question_id,question=case.question,answerable=case.answerable,
                relevant_chunk_ids=gold,**{mode:{"retrieved_chunk_ids":ids,"metrics":deepcopy(canonical)} for mode in MODES}))
        return benchmark,saved

    def test_saved_scores_and_negative_exclusion(self):
        benchmark,saved=self.fixture()
        result=rescore(benchmark,saved)
        self.assertEqual(result["answerable_count"],1)
        for mode in MODES:
            self.assertEqual(result["aggregates"][mode]["canonical"]["mrr"],0)
            self.assertEqual(result["aggregates"][mode]["evidence"]["mrr"],1)
            self.assertEqual(result["aggregates"][mode]["evidence"]["complete_at_1"],1)
            self.assertIsNone(result["queries"][1]["modes"][mode]["evidence"]["complete_at_1"])

    def test_source_mismatch_fails(self):
        benchmark,saved=self.fixture()
        saved["queries"][0]["question"]="changed"
        with self.assertRaises(ValueError): rescore(benchmark,saved)
        benchmark,saved=self.fixture()
        saved["queries"][0]["hybrid"]["metrics"]["reciprocal_rank"]=1
        with self.assertRaises(ValueError): rescore(benchmark,saved)
