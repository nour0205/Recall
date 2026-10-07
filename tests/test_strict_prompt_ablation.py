"""Offline tests of the controlled prompt treatment; no live model calls."""

import ast
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import inspect
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from evaluation.generation_benchmark import CASE_IDS, canonical_hash, file_hash
from evaluation import run_strict_prompt_ablation as strict


def client(answer="Mock answer [S1].", usage=True):
    response = SimpleNamespace(
        id="mock-response", model="gpt-4o-mini-2024-07-18", system_fingerprint="mock-fingerprint",
        choices=[SimpleNamespace(message=SimpleNamespace(content=answer), finish_reason="stop")],
        usage=SimpleNamespace(model_dump=lambda **kwargs: {
            "prompt_tokens": 200, "completion_tokens": 10, "total_tokens": 210,
        }) if usage else None,
    )
    instance = Mock()
    instance.chat.completions.create.return_value = response
    return instance


class StrictPromptAblationTests(unittest.TestCase):
    def setUp(self):
        _, _, self.baseline = strict.frozen_inputs()
        self.prompt = strict.load_prompt()
        self.hashes = {"strict_prompt_definition_sha256": file_hash(strict.PROMPT_PATH)}

    def run_one(self, index=0, api=None, checkpoint=None, original=None):
        return strict.run_case(
            original if original is not None else self.baseline["queries"][index],
            api if api is not None else client(), self.prompt, self.baseline["configuration"], self.hashes,
            checkpoint if checkpoint is not None else Mock(),
        )

    def test_all_19_contexts_structurally_identical_and_text_bytes_reused(self):
        strict.validate_frozen_baseline(self.baseline)
        for i, original in enumerate(self.baseline["queries"]):
            row = self.run_one(i)
            for field in strict.CONTEXT_FIELDS:
                self.assertEqual(row[field], original[field])
                self.assertEqual(json.dumps(row[field], ensure_ascii=False).encode("utf-8"),
                                 json.dumps(original[field], ensure_ascii=False).encode("utf-8"))
            block = strict.context_block(original["retrieved_context_chunks"])
            self.assertIn(block.encode("utf-8"), original["prompt_messages"][1]["content"].encode("utf-8"))
            self.assertIn(block.encode("utf-8"), row["prompt_messages"][1]["content"].encode("utf-8"))
            self.assertEqual(row["context_structural_sha256"], canonical_hash(original["retrieved_context_chunks"]))
            self.assertEqual(row["context_prompt_bytes_sha256"], hashlib.sha256(block.encode("utf-8")).hexdigest())
            self.assertIsNot(row["retrieved_context_chunks"], original["retrieved_context_chunks"])

    def test_question_order_and_exact_model_request_settings(self):
        api = client()
        rows = [self.run_one(i, api=api) for i in range(19)]
        self.assertEqual(tuple(row["question_id"] for row in rows), CASE_IDS)
        self.assertEqual(api.chat.completions.create.call_count, 19)
        for original, call in zip(self.baseline["queries"], api.chat.completions.create.call_args_list):
            kwargs = call.kwargs
            self.assertEqual(set(kwargs), {"messages", "model", "temperature", "max_tokens"})
            self.assertEqual({key: kwargs[key] for key in ("model", "temperature", "max_tokens")},
                             strict.request_parameters(original))
            self.assertIn(original["question"], kwargs["messages"][1]["content"])

    def test_reference_answers_and_labels_never_passed_to_generator(self):
        marker = "SECRET_REFERENCE_ANSWER_LABEL_DO_NOT_SEND"
        original = deepcopy(self.baseline["queries"][0])
        expected = self.run_one(original=original)["prompt_messages"]
        original["reference_answer"] = marker
        original["generated_answer"] = marker
        original["required_points"] = [{"text": marker}]
        original["required_point_evidence"] = [{"reviewer_notes": marker}]
        original["human_evaluation"] = {"correctness": marker}
        api = client()
        actual = self.run_one(original=original, api=api)["prompt_messages"]
        self.assertEqual(actual, expected)
        self.assertNotIn(marker, json.dumps(api.chat.completions.create.call_args.kwargs))
        self.assertEqual(tuple(inspect.signature(strict.build_strict_messages).parameters),
                         ("question", "context_chunks", "prompt"))

    def test_prompt_version_definition_and_exact_refusal_instruction_recorded(self):
        row = self.run_one()
        self.assertEqual(row["prompt_version"], "grounded_strict_v1")
        self.assertEqual(row["prompt_definition_sha256"], file_hash(strict.PROMPT_PATH))
        system = row["prompt_messages"][0]["content"]
        self.assertEqual(system, self.prompt["system"])
        self.assertIn("your entire response must be exactly:\nI don't know.\nStop immediately after this sentence.", system)
        self.assertIn("Do not continue with supporting points, review tips, related information, explanations, or citations after a refusal.", system)
        for phrase in ("Use ONLY facts explicitly supported", "Do not create generic Supporting Points",
                       "Do not infer facts from general model knowledge", "Preserve qualifiers", "short, direct answer",
                       "explanations, mechanisms, examples, formulas, consequences, recommendations, or background knowledge"):
            self.assertIn(phrase, system)

    def test_labels_and_evidence_not_rescored(self):
        for i in range(19):
            row = self.run_one(i)
            self.assertTrue(all(value is None for value in row["human_evaluation"].values()))
            self.assertEqual(row["required_point_evidence"], self.baseline["queries"][i]["required_point_evidence"])
            self.assertFalse(row["retrieval_executed"])

    def test_checkpoint_saves_exact_prompt_before_single_request(self):
        api = client()
        response = api.chat.completions.create.return_value
        snapshots = []
        def request(**kwargs):
            self.assertEqual(snapshots[-1]["status"], "generating")
            self.assertIsNone(snapshots[-1]["generated_answer"])
            self.assertEqual(snapshots[-1]["prompt_messages"], kwargs["messages"])
            self.assertEqual(snapshots[-1]["source_mapping"], self.baseline["queries"][0]["source_mapping"])
            return response
        api.chat.completions.create.side_effect = request
        self.run_one(api=api, checkpoint=lambda row: snapshots.append(deepcopy(row)))
        api.chat.completions.create.assert_called_once()
        self.assertEqual([row["status"] for row in snapshots], ["generating", "completed"])

    def test_failure_has_no_retry_fallback_or_quality_scoring(self):
        api = client()
        api.chat.completions.create.side_effect = RuntimeError("private data")
        row = self.run_one(api=api)
        api.chat.completions.create.assert_called_once()
        self.assertEqual(row["status"], "generation_failed")
        self.assertNotIn("private data", json.dumps(row))
        self.assertIsNone(row["generated_answer"])
        self.assertTrue(all(value is None for value in row["human_evaluation"].values()))

    def test_operational_length_comparison_uses_matching_cases_only(self):
        row = self.run_one(api=client("two words", usage=False))
        failed = self.run_one(1)
        failed["status"] = "generation_failed"
        summary = strict.operational_summary([row, failed], self.baseline["queries"])
        comparison = summary["answer_length_comparison"]
        self.assertEqual(comparison["paired_case_count"], 1)
        self.assertEqual(comparison["grounded_strict_v1"], {"mean_characters": 9, "mean_whitespace_words": 2})
        original = self.baseline["queries"][0]["generated_answer"]
        self.assertEqual(comparison["baseline"]["mean_characters"], len(original))
        self.assertEqual(comparison["baseline"]["mean_whitespace_words"], len(original.split()))
        self.assertEqual(summary["token_usage"]["available_case_count"], 0)
        self.assertTrue(set(strict.QUALITY_FIELDS).isdisjoint(summary))

    def test_zero_completed_summary_is_defined(self):
        summary = strict.operational_summary([], self.baseline["queries"])
        self.assertEqual(summary["completed_generations"], 0)
        self.assertIsNone(summary["generation_latency_seconds"]["mean"])
        self.assertIsNone(summary["answer_length_comparison"]["strict_to_baseline_character_ratio"])

    def test_changed_settings_context_order_and_mapping_rejected(self):
        mutations = [
            lambda b: b["configuration"].update(model="other"),
            lambda b: b["configuration"].update(temperature=0.5),
            lambda b: b["configuration"].update(max_tokens=100),
            lambda b: b["queries"].reverse(),
            lambda b: b["queries"][0]["retrieved_context_chunks"].reverse(),
            lambda b: b["queries"][0]["source_mapping"]["[S1]"].update(chunk_id="changed"),
            lambda b: b["queries"][0]["retrieved_context_chunks"][0].update(text="changed"),
        ]
        for change in mutations:
            altered = deepcopy(self.baseline)
            change(altered)
            with self.subTest(change=change), self.assertRaises(ValueError):
                strict.validate_frozen_baseline(altered)

    def test_existing_output_prevents_factory_and_requests(self):
        factory = Mock(side_effect=AssertionError("Must not construct API client"))
        with TemporaryDirectory() as directory:
            path = Path(directory) / "strict.json"
            path.write_text("historical artifact", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                strict.main(path, client_factory=factory)
            self.assertEqual(path.read_text(encoding="utf-8"), "historical artifact")
        factory.assert_not_called()

    def test_full_offline_run_changes_only_prompt_and_preserves_production_files(self):
        before = strict.protected_hashes()
        api = client()
        factory = Mock(return_value=api)
        with TemporaryDirectory() as directory, redirect_stdout(StringIO()):
            path = Path(directory) / "strict.json"
            strict.main(path, client_factory=factory)
            saved = json.loads(path.read_text(encoding="utf-8"))
        factory.assert_called_once_with(max_retries=0, timeout=60)
        self.assertEqual(api.chat.completions.create.call_count, 19)
        api.close.assert_called_once()
        self.assertEqual(saved["run_status"], "completed")
        self.assertEqual(saved["configuration"], {**self.baseline["configuration"], "prompt_version": "grounded_strict_v1"})
        self.assertEqual(saved["prompt_definition"], self.prompt)
        self.assertEqual(saved["protected_file_hashes_before"], before)
        self.assertEqual(saved["protected_file_hashes_after"], before)
        self.assertTrue(saved["protected_files_unchanged"])
        self.assertEqual(before, strict.protected_hashes())
        self.assertEqual(saved["quality_scoring"], "not_performed")
        self.assertEqual(saved["embedding_calls"], 0)
        self.assertFalse(saved["retrieval_executed"])

    def test_no_retrieval_production_planner_or_embedding_imports(self):
        tree = ast.parse(Path(strict.__file__).read_text(encoding="utf-8"))
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.append(node.module)
        forbidden = ("app", "chromadb", "whoosh", "evaluation.retrieval", "evaluation.run_generation_baseline",
                     "evaluation.semantic_reranker", "ragas")
        self.assertTrue(all(not name.startswith(forbidden) for name in names))

    def test_fresh_process_completes_with_retrieval_imports_blocked(self):
        # Fresh interpreter proves the absence of imports despite suite caches.
        script = '''
import importlib.abc, sys
from types import SimpleNamespace
class BlockRetrieval(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        forbidden = ("app", "chromadb", "whoosh", "evaluation.retrieval", "evaluation.run_generation_baseline", "evaluation.semantic_reranker", "openai")
        if fullname.startswith(forbidden):
            raise AssertionError("Forbidden dependency: " + fullname)
sys.meta_path.insert(0, BlockRetrieval())
from evaluation.run_strict_prompt_ablation import main
response = SimpleNamespace(id="fake", model="gpt-4o-mini", system_fingerprint=None, usage=None,
    choices=[SimpleNamespace(message=SimpleNamespace(content="Fake fixture."), finish_reason="stop")])
class API:
    def __init__(self):
        self.calls=0
        self.chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))
    def create(self, **kwargs):
        self.calls += 1
        return response
    def close(self):
        assert self.calls == 19
api=API()
main(sys.argv[1], client_factory=lambda **kwargs: api)
'''
        with TemporaryDirectory() as directory:
            completed = subprocess.run([sys.executable, "-c", script, str(Path(directory) / "strict.json")],
                                       capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
