"""The production prompt must be the prompt the evaluation measured."""
import json
import os
from pathlib import Path
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test-placeholder")

from app.orchestration import prompts


class ProductionPromptTest(unittest.TestCase):
    def test_production_prompt_is_the_evaluated_strict_v2_prompt(self):
        evaluated = json.loads(Path("evaluation/prompts/grounded_strict_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(prompts.PROMPT_VERSION, evaluated["prompt_version"])
        self.assertEqual(prompts.SYSTEM_PROMPT, evaluated["system"])
        self.assertEqual(prompts.USER_TEMPLATE, evaluated["user_template"])


if __name__ == "__main__":
    unittest.main()
