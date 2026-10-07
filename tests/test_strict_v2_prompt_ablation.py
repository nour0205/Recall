"""Offline strict-v2 controls; fake answers are not quality labels."""
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

from evaluation import run_strict_v2_prompt_ablation as candidate
from evaluation import run_strict_prompt_ablation as frozen
from evaluation.generation_benchmark import CASE_IDS, file_hash
from tests.test_strict_prompt_ablation import client


class StrictV2Tests(unittest.TestCase):
    def test_strict_v1_is_preserved_verbatim_with_only_six_targeted_additions(self):
        old = frozen.load_prompt()
        new = frozen.load_prompt(candidate.PROMPT_PATH, candidate.PROMPT_VERSION)
        self.assertEqual(new["user_template"], old["user_template"])
        self.assertTrue(new["system"].startswith(old["system"] + "\n\n"))
        addition = new["system"][len(old["system"]):]
        self.assertEqual(len([line for line in addition.splitlines() if line[:2].isdigit()]), 6)
        for phrase in ("answer each requested part", "identification and a supported explanation/mechanism",
                       "Do not refuse when", "solely for brevity", "not explicitly requested",
                       "dependency/problem itself"):
            self.assertIn(phrase, addition)
        self.assertIn("I don't know.\nStop immediately after this sentence.", new["system"])
        self.assertNotIn("retrieval_", json.dumps(new))

    def test_full_mock_pass_preserves_all_controls_and_no_scores(self):
        before = candidate.protected_hashes()
        _, _, baseline = frozen.frozen_inputs()
        api = client()
        factory = Mock(return_value=api)
        with TemporaryDirectory() as directory, redirect_stdout(StringIO()):
            path = Path(directory)/"run.json"
            candidate.main(path, factory)
            run = json.loads(path.read_text(encoding="utf-8"))
        factory.assert_called_once_with(max_retries=0, timeout=60)
        self.assertEqual(api.chat.completions.create.call_count, 19)
        self.assertEqual(tuple(r["question_id"] for r in run["queries"]), CASE_IDS)
        self.assertEqual(run["configuration"], {**baseline["configuration"], "prompt_version": candidate.PROMPT_VERSION})
        self.assertTrue(run["protected_files_unchanged"])
        self.assertEqual(before, candidate.protected_hashes())
        self.assertFalse(run["retrieval_executed"])
        self.assertEqual(run["embedding_calls"], 0)
        self.assertEqual(run["quality_scoring"], "not_performed")
        self.assertEqual(set(run["operational_summary"]["efficiency_comparison"]), {"baseline", "grounded_strict_v1", "grounded_balanced_v2", candidate.PROMPT_VERSION})
        for old, row, call in zip(baseline["queries"], run["queries"], api.chat.completions.create.call_args_list):
            for field in frozen.CONTEXT_FIELDS:
                self.assertEqual(json.dumps(old[field], ensure_ascii=False).encode(), json.dumps(row[field], ensure_ascii=False).encode())
            block = frozen.context_block(old["retrieved_context_chunks"]).encode()
            self.assertIn(block, row["prompt_messages"][1]["content"].encode())
            self.assertEqual(row["prompt_version"], candidate.PROMPT_VERSION)
            self.assertEqual(row["prompt_definition_sha256"], file_hash(candidate.PROMPT_PATH))
            self.assertTrue(all(v is None for v in row["human_evaluation"].values()))
            self.assertEqual(frozen.request_parameters(row), frozen.request_parameters(old))
            self.assertEqual(set(call.kwargs), {"messages", "model", "temperature", "max_tokens"})

    def test_references_required_points_and_old_answers_never_reach_model(self):
        _, _, baseline = frozen.frozen_inputs()
        row = deepcopy(baseline["queries"][0])
        prompt = frozen.load_prompt(candidate.PROMPT_PATH, candidate.PROMPT_VERSION)
        expected = frozen.build_strict_messages(row["question"], row["retrieved_context_chunks"], prompt)
        for key in ("reference_answer", "required_points", "required_point_evidence", "generated_answer", "human_evaluation"):
            row[key] = "SECRET_REFERENCE_MARKER"
        api = client()
        saved = frozen.run_case(row, api, prompt, baseline["configuration"], {"prompt_definition_sha256": "fixture"}, Mock())
        self.assertEqual(saved["prompt_messages"], expected)
        self.assertNotIn("SECRET_REFERENCE_MARKER", json.dumps(api.chat.completions.create.call_args.kwargs))

    def test_existing_output_blocks_requests(self):
        factory = Mock()
        with TemporaryDirectory() as directory:
            path = Path(directory)/"existing.json"
            path.write_text("historical", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                candidate.main(path, factory)
            self.assertEqual(path.read_text(encoding="utf-8"), "historical")
        factory.assert_not_called()

    def test_fresh_process_cannot_import_retrieval_or_production(self):
        script = '''
import importlib.abc, sys
from types import SimpleNamespace
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("app", "chromadb", "whoosh", "evaluation.retrieval", "evaluation.run_generation_baseline", "evaluation.semantic_reranker", "openai", "ragas")):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Block())
from evaluation.run_strict_v2_prompt_ablation import main
response=SimpleNamespace(id="fake",model="gpt-4o-mini",system_fingerprint=None,usage=None,choices=[SimpleNamespace(message=SimpleNamespace(content="Fixture."),finish_reason="stop")])
api=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: response)),close=lambda: None)
main(sys.argv[1],client_factory=lambda **kw: api)
'''
        with TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-c", script, str(Path(directory)/"run.json")], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
