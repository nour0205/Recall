"""Offline checks of frozen labels, prompt isolation, retrieval, and recording."""

import ast
from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from app.schemas.retrieval import RetrievedChunk
from evaluation.generation_benchmark import (
    CASE_IDS, REFUSAL_IDS, REFERENCE_PATH, RETRIEVAL_PATH, canonical_hash,
    load_generation_benchmark, point_evidence,
)
from evaluation import run_generation_baseline as runner


def chunk(cid, document="same_document", text="supplied notes"):
    return RetrievedChunk(
        id=cid, chunk_id=cid, document_id=document, text=text,
        metadata={"chunk_id": cid, "document_id": document, "source": "notes", "owner": "student"},
        retrieval_type="hybrid", hybrid_score=0.03,
    )


def fake_client(answer="A supported answer [S1].", usage=True):
    response = SimpleNamespace(
        id="response-id", model="gpt-4o-mini-test-snapshot", system_fingerprint="fingerprint",
        choices=[SimpleNamespace(message=SimpleNamespace(content=answer), finish_reason="stop")],
        usage=SimpleNamespace(model_dump=lambda **kwargs: {
            "prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120,
        }) if usage else None,
    )
    client = Mock()
    client.chat.completions.create.return_value = response
    return client


class GenerationBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.benchmark, self.references = load_generation_benchmark()

    def test_exact_19_cases_gap_and_refusal_identities(self):
        self.assertEqual(len(self.references.cases), 19)
        self.assertEqual(tuple(c.question_id for c in self.references.cases), CASE_IDS)
        self.assertNotIn("retrieval_018", CASE_IDS)
        self.assertEqual({c.question_id for c in self.references.cases if c.expected_behavior == "refuse"}, REFUSAL_IDS)
        self.assertEqual(sum(c.answerable for c in self.benchmark.cases), 16)

    def test_dimensions_separate_and_prompt_compliance_optional(self):
        self.assertTrue(set(runner.QUALITY_DIMENSIONS) <= self.references.rubric.keys())
        self.assertNotIn("prompt_compliance", runner.QUALITY_DIMENSIONS)
        self.assertTrue(self.references.rubric["prompt_compliance"]["optional"])
        for suffix in ("005", "019", "020"):
            case = next(c for c in self.references.cases if c.question_id == "retrieval_" + suffix)
            self.assertEqual(case.reference_answer, "I don't know.")
            self.assertFalse(case.citation_expectation.source_support_required)

    def test_all_factual_points_map_to_existing_groups(self):
        for ref, case in zip(self.references.cases, self.benchmark.cases):
            groups = {g.group_id for g in case.evidence_groups}
            mapped = {gid for p in ref.required_points for gid in p.evidence_group_ids}
            self.assertEqual(mapped, groups)
            for p in ref.required_points:
                self.assertEqual(bool(p.evidence_group_ids), case.answerable)

    def test_invalid_frozen_data_fails_loading(self):
        original = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
        mutations = [
            lambda d: d["cases"].pop(),
            lambda d: d["cases"][0].update(question_id="retrieval_018"),
            lambda d: d["cases"][4].update(expected_behavior="answer"),
            lambda d: d["cases"][0]["required_points"][0].update(evidence_group_ids=["unknown"]),
            lambda d: d.update(retrieval_benchmark_sha256="wrong"),
            lambda d: d["rubric"]["prompt_compliance"].update(optional=False),
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "references.json"
            for change in mutations:
                modified = deepcopy(original)
                change(modified)
                path.write_text(json.dumps(modified), encoding="utf-8")
                with self.subTest(change=change), self.assertRaises(ValueError):
                    load_generation_benchmark(path, RETRIEVAL_PATH)

    def test_partial_evidence_and_document_identity(self):
        case, ref = self.benchmark.cases[14], self.references.cases[14]
        atomicity = case.evidence_groups[0].acceptable_chunks[0]
        evidence = point_evidence(ref, case, [chunk(atomicity.chunk_id, atomicity.document_id)])
        self.assertEqual([p["sufficient_retrieved_evidence"] for p in evidence], [True, False])
        wrong_doc = point_evidence(ref, case, [chunk(atomicity.chunk_id, "wrong_document")])
        self.assertFalse(wrong_doc[0]["sufficient_retrieved_evidence"])
        refusal = point_evidence(self.references.cases[4], self.benchmark.cases[4], [])
        self.assertIsNone(refusal[0]["sufficient_retrieved_evidence"])

    def test_explicit_ipc_requires_explicit_evidence(self):
        case, ref = self.benchmark.cases[2], self.references.cases[2]
        basic = chunk("0c277ad4-37e2-4378-ae31-64e52a11d86a", "os_processes_threads_scheduling")
        evidence = point_evidence(ref, case, [basic])
        self.assertEqual([p["sufficient_retrieved_evidence"] for p in evidence], [True, True, False, True])
        complete = chunk("a4d8fe4d-300d-49b7-b7a9-c573f06af200", "os_process_vs_thread")
        self.assertTrue(all(p["sufficient_retrieved_evidence"] for p in point_evidence(ref, case, [complete])))

    def test_fold_rotation_does_not_imply_single_split_evidence(self):
        case, ref = self.benchmark.cases[12], self.references.cases[12]
        rotation = chunk("238ddbf4-a7b9-4647-b485-79a96e6a48d5", "ml_bias_variance_generalization")
        self.assertEqual([p["sufficient_retrieved_evidence"] for p in point_evidence(ref, case, [rotation])],
                         [True, True, False])


class GenerationRunnerTests(unittest.TestCase):
    def setUp(self):
        self.benchmark, self.references = load_generation_benchmark()
        self.chunks = [chunk(f"chunk-{i}", text=f"Note passage {i}.") for i in range(5)]

    def run_one(self, client=None, retrieve=None, checkpoint=None, index=0):
        return runner.run_case(
            self.benchmark.cases[index], self.references.cases[index], object(),
            client if client is not None else fake_client(),
            retrieve if retrieve is not None else Mock(return_value=self.chunks),
            checkpoint if checkpoint is not None else Mock(), {"test_hash": "frozen"},
        )

    def test_all_19_questions_each_make_one_request_with_required_fields(self):
        client = fake_client()
        retrieve = Mock(return_value=self.chunks)
        rows = [self.run_one(client=client, retrieve=retrieve, index=i) for i in range(19)]
        self.assertEqual(client.chat.completions.create.call_count, 19)
        self.assertEqual(retrieve.call_count, 19)
        required = {
            "question_id", "question", "expected_behavior", "retrieved_context_chunks",
            "retrieved_chunk_ids", "source_mapping", "required_point_evidence",
            "context_sufficient_for_full_answer", "generated_answer", "model", "response_model",
            "temperature", "max_tokens", "prompt_version", "prompt_messages", "prompt_sha256",
            "retrieval_mode", "top_k", "candidate_k", "generation_latency_seconds", "token_usage",
            "timestamp_utc", "hashes", "human_evaluation", "status", "error",
        }
        for row in rows:
            self.assertTrue(required <= row.keys())
            self.assertEqual(row["status"], "completed")
            self.assertEqual(row["retrieved_chunk_ids"], [c.chunk_id for c in self.chunks])
            self.assertTrue(all(value is None for value in row["human_evaluation"].values()))
            self.assertGreaterEqual(row["generation_latency_seconds"], 0)
            self.assertEqual(row["token_usage"]["total_tokens"], 120)
        for call in retrieve.call_args_list:
            self.assertEqual(call.kwargs, {"mode": "hybrid", "k": 5, "candidate_k": 10})
        for call, case in zip(client.chat.completions.create.call_args_list, self.benchmark.cases):
            self.assertEqual(set(call.kwargs), {"model", "messages", "temperature", "max_tokens"})
            self.assertEqual(call.kwargs["model"], "gpt-4o-mini")
            self.assertEqual(call.kwargs["temperature"], 0)
            self.assertEqual(call.kwargs["max_tokens"], 800)
            self.assertIn(case.question, call.kwargs["messages"][1]["content"])

    def test_reference_and_labels_never_enter_prompt(self):
        client = fake_client()
        original = self.run_one(client=client)["prompt_messages"]
        marker = "REFERENCE_LABEL_SENTINEL_DO_NOT_SEND"
        ref = self.references.cases[0]
        ref.reference_answer = marker
        ref.review_notes = marker
        ref.forbidden_or_unsupported_points = [marker]
        for point in ref.required_points:
            point.text = marker
        self.references.rubric["correctness"]["rule"] = marker
        modified = self.run_one(client=client)["prompt_messages"]
        self.assertEqual(original, modified)
        self.assertNotIn(marker, json.dumps(client.chat.completions.create.call_args.kwargs))
        # A narrow signature prevents a reference/labels parameter at the API boundary.
        import inspect
        self.assertEqual(tuple(inspect.signature(runner.generate).parameters), ("client", "question", "chunks"))

    def test_stable_source_mapping_and_no_document_deduplication(self):
        row = self.run_one()
        self.assertEqual(len(row["retrieved_context_chunks"]), 5)
        self.assertEqual(list(row["source_mapping"]), [f"[S{i}]" for i in range(1, 6)])
        user = row["prompt_messages"][1]["content"]
        previous = -1
        for i, c in enumerate(self.chunks, 1):
            self.assertEqual(row["source_mapping"][f"[S{i}]"]["chunk_id"], c.chunk_id)
            self.assertEqual(row["retrieved_context_chunks"][i-1]["metadata"], c.metadata)
            position = user.index(f"[S{i}] DOCUMENT: {c.document_id}\nCONTENT:\n{c.text}")
            self.assertGreater(position, previous)
            previous = position
        self.assertEqual(row["prompt_sha256"], canonical_hash(row["prompt_messages"]))
        self.assertEqual(row["source_mapping"], runner.source_mapping(self.chunks))

    def test_evidence_is_checkpointed_before_model_request(self):
        checkpoints = []
        client = fake_client()
        response = client.chat.completions.create.return_value
        def request(**kwargs):
            self.assertEqual(checkpoints[-1]["status"], "generating")
            self.assertIsNone(checkpoints[-1]["generated_answer"])
            self.assertEqual(len(checkpoints[-1]["required_point_evidence"]), 1)
            self.assertEqual(checkpoints[-1]["prompt_messages"], kwargs["messages"])
            return response
        client.chat.completions.create.side_effect = request
        self.run_one(client=client, checkpoint=lambda row: checkpoints.append(deepcopy(row)))
        self.assertEqual([r["status"] for r in checkpoints], ["retrieving", "generating", "completed"])

    def test_api_failure_recorded_once_without_fallback(self):
        client = fake_client()
        client.chat.completions.create.side_effect = RuntimeError("private error text")
        row = self.run_one(client=client)
        self.assertEqual(client.chat.completions.create.call_count, 1)
        self.assertEqual(row["status"], "generation_failed")
        self.assertEqual(row["error"]["stage"], "generation")
        self.assertNotIn("private error text", json.dumps(row))
        self.assertIsNone(row["generated_answer"])
        self.assertIsNotNone(row["generation_latency_seconds"])

    def test_retrieval_failure_makes_no_generation_request(self):
        client = fake_client()
        row = self.run_one(client=client, retrieve=Mock(side_effect=RuntimeError("unavailable")))
        client.chat.completions.create.assert_not_called()
        self.assertEqual(row["status"], "retrieval_failed")
        self.assertIsNone(row["context_sufficient_for_full_answer"])

    def test_invalid_context_rejected_and_empty_context_still_uses_grounded_prompt(self):
        client = fake_client()
        row = self.run_one(client=client, retrieve=Mock(return_value=self.chunks + [chunk("sixth")]))
        self.assertEqual(row["status"], "retrieval_failed")
        client.chat.completions.create.assert_not_called()
        empty = self.run_one(retrieve=Mock(return_value=[]))
        self.assertEqual(empty["status"], "completed")
        self.assertFalse(empty["context_sufficient_for_full_answer"])
        self.assertEqual(empty["source_mapping"], {})

    def test_operational_summary_is_unscored_and_usage_optional(self):
        rows = [self.run_one(), self.run_one(client=fake_client(usage=False))]
        summary = runner.operational_summary(rows)
        self.assertEqual(summary["completed_generations"], 2)
        self.assertEqual(summary["token_usage"]["available_case_count"], 1)
        self.assertEqual(summary["token_usage"]["total_tokens"], 120)
        self.assertTrue(set(runner.QUALITY_DIMENSIONS).isdisjoint(summary))

    def test_existing_result_prevents_requests_and_is_unchanged(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "baseline.json"
            path.write_text("historical output", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                runner.main(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "historical output")

    def test_no_planner_fallback_or_semantic_reranker_imports(self):
        forbidden = {"app.api.main", "app.orchestration.planner", "app.rag.pipeline",
                     "evaluation.semantic_reranker", "evaluation.run_semantic_ablation"}
        tree = ast.parse(Path(runner.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(node.module, forbidden)
            if isinstance(node, ast.Import):
                self.assertTrue(forbidden.isdisjoint(alias.name for alias in node.names))
        config = runner.configuration()
        self.assertFalse(config["planner"])
        self.assertIsNone(config["reranker"])
        self.assertFalse(config["application_fallbacks"])

    def test_real_hybrid_branch_fuses_candidates_and_never_reranks(self):
        # Keep application-client creation and embedding calls out of offline tests.
        stub = ModuleType("app.embeddings.embedder")
        stub.embed_texts = Mock(side_effect=AssertionError("No embedding call in offline test"))
        with patch.dict(sys.modules, {"app.embeddings.embedder": stub}):
            from evaluation import retrieval
        vectors = [{"id": f"v{i}", "rank": i+1, "text": "vector passage",
                    "metadata": {"chunk_id": f"v{i}", "document_id": "vector_doc"}} for i in range(10)]
        lexical = [{"id": f"b{i}", "rank": i+1, "text": "lexical passage",
                    "metadata": {"chunk_id": f"b{i}", "document_id": "lexical_doc"}} for i in range(10)]
        with patch.object(retrieval, "retrieve_vector_candidates", return_value=vectors) as vector, \
             patch.object(retrieval, "retrieve_bm25_candidates", return_value=lexical) as bm25, \
             patch.object(retrieval, "reciprocal_rank_fusion", wraps=retrieval.reciprocal_rank_fusion) as fusion, \
             patch.object(retrieval, "rerank_items", side_effect=AssertionError("Reranker must not run")) as rerank:
            row = self.run_one(retrieve=retrieval.retrieve)
        vector.assert_called_once()
        bm25.assert_called_once()
        self.assertEqual(vector.call_args.kwargs["k"], 10)
        self.assertEqual(bm25.call_args.kwargs["k"], 10)
        fusion.assert_called_once_with(vectors, lexical)
        rerank.assert_not_called()
        self.assertEqual(len(row["retrieved_context_chunks"]), 5)
        self.assertEqual(row["retrieved_chunk_ids"], ["v0", "b0", "v1", "b1", "v2"])
        self.assertEqual(row["retrieval_algorithm"], "Vector + BM25 + RRF")


if __name__ == "__main__":
    unittest.main()
