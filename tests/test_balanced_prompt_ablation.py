"""Offline controls for the balanced prompt; never calls the live API."""
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from evaluation import run_balanced_prompt_ablation as balanced
from evaluation import run_strict_prompt_ablation as frozen
from evaluation.generation_benchmark import CASE_IDS
from tests.test_strict_prompt_ablation import client


class BalancedPromptTests(unittest.TestCase):
    def test_full_pass_preserves_all_controls_and_leaves_scores_empty(self):
        before = balanced.protected_hashes()
        _, _, baseline = frozen.frozen_inputs()
        api = client()
        factory = Mock(return_value=api)
        with TemporaryDirectory() as directory, redirect_stdout(StringIO()):
            path = Path(directory) / "balanced.json"
            balanced.main(path, factory)
            run = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(tuple(r["question_id"] for r in run["queries"]), CASE_IDS)
        self.assertEqual(run["configuration"], {**baseline["configuration"], "prompt_version": balanced.PROMPT_VERSION})
        factory.assert_called_once_with(max_retries=0, timeout=60)
        self.assertEqual(api.chat.completions.create.call_count, 19)
        self.assertTrue(run["protected_files_unchanged"])
        self.assertEqual(before, balanced.protected_hashes())
        self.assertFalse(run["retrieval_executed"])
        self.assertEqual(run["quality_scoring"], "not_performed")
        for old, row, call in zip(baseline["queries"], run["queries"], api.chat.completions.create.call_args_list):
            for field in frozen.CONTEXT_FIELDS:
                self.assertEqual(json.dumps(old[field], ensure_ascii=False).encode(), json.dumps(row[field], ensure_ascii=False).encode())
            self.assertIn(frozen.context_block(old["retrieved_context_chunks"]).encode(), row["prompt_messages"][1]["content"].encode())
            self.assertEqual(row["prompt_version"], balanced.PROMPT_VERSION)
            self.assertTrue(all(v is None for v in row["human_evaluation"].values()))
            self.assertEqual(set(call.kwargs), {"messages", "model", "temperature", "max_tokens"})
            self.assertEqual(frozen.request_parameters(row), frozen.request_parameters(old))
        self.assertEqual(set(run["operational_summary"]["efficiency_comparison"]), {"baseline", "grounded_strict_v1", balanced.PROMPT_VERSION})

    def test_prompt_rules_and_unchanged_user_template(self):
        prompt = frozen.load_prompt(balanced.PROMPT_PATH, balanced.PROMPT_VERSION)
        self.assertEqual(prompt["user_template"], frozen.load_prompt()["user_template"])
        for phrase in ("I don't know.\nStop immediately after this sentence.",
                       "answer ALL supported parts", "Conciseness must not reduce completeness",
                       "cover each side", "what plus why/how", "Do not expose",
                       "Do not refuse if", "requested essential part", "Preserve qualifiers",
                       "Every substantive factual claim", "Use ONLY facts explicitly supported",
                       "Do not infer facts from general model knowledge"):
            self.assertIn(phrase, prompt["system"])

    def test_reference_and_labels_excluded_from_request(self):
        _, _, baseline = frozen.frozen_inputs()
        row = deepcopy(baseline["queries"][0])
        prompt = frozen.load_prompt(balanced.PROMPT_PATH, balanced.PROMPT_VERSION)
        expected = frozen.build_strict_messages(row["question"], row["retrieved_context_chunks"], prompt)
        for field in ("reference_answer", "required_points", "human_evaluation", "generated_answer"):
            row[field] = "SECRET_REFERENCE_MARKER"
        api = client()
        actual = frozen.run_case(row, api, prompt, baseline["configuration"], {"prompt_definition_sha256": "fixture"}, Mock())
        self.assertEqual(actual["prompt_messages"], expected)
        self.assertNotIn("SECRET_REFERENCE_MARKER", json.dumps(api.chat.completions.create.call_args.kwargs))

    def test_existing_output_blocks_any_api_construction(self):
        factory = Mock()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "existing.json"
            path.write_text("historical", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                balanced.main(path, factory)
            self.assertEqual(path.read_text(encoding="utf-8"), "historical")
        factory.assert_not_called()

    def test_fresh_process_blocks_retrieval_and_production_imports(self):
        script = '''
import importlib.abc, sys
from types import SimpleNamespace
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("app", "chromadb", "whoosh", "evaluation.retrieval", "evaluation.run_generation_baseline", "evaluation.semantic_reranker", "openai", "ragas")):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Block())
from evaluation.run_balanced_prompt_ablation import main
response=SimpleNamespace(id="fake",model="gpt-4o-mini",system_fingerprint=None,usage=None,choices=[SimpleNamespace(message=SimpleNamespace(content="Fixture."),finish_reason="stop")])
api=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: response)),close=lambda: None)
main(sys.argv[1],client_factory=lambda **kw: api)
'''
        with TemporaryDirectory() as directory:
            process = subprocess.run([sys.executable, "-c", script, str(Path(directory)/"run.json")], capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
