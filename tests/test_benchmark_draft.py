"""Draft v3 benchmark: evidence must be quoted verbatim from the demo notes."""
import copy
import unittest

from evaluation import benchmark_draft as draft_lib


class BenchmarkDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft = draft_lib.load()
        cls.notes = draft_lib.note_texts()

    def test_draft_is_valid(self):
        self.assertEqual(draft_lib.validate(self.draft, self.notes), [])

    def test_every_category_is_used_and_refusals_are_well_represented(self):
        used = {c["category"] for c in self.draft["cases"]}
        self.assertEqual(used, set(self.draft["categories"]))
        refusals = sum(c["expected_behavior"] == "refuse" for c in self.draft["cases"])
        self.assertGreaterEqual(refusals, 10)

    def test_validator_rejects_an_invented_quote(self):
        broken = copy.deepcopy(self.draft)
        broken["cases"][0]["required_points"][0]["evidence"][0]["quote"] = "Gradient descent always converges."
        problems = draft_lib.validate(broken, self.notes)
        self.assertTrue(any("quote not found" in p for p in problems))

    def test_validator_rejects_refuse_cases_with_points_or_a_non_exact_reference(self):
        broken = copy.deepcopy(self.draft)
        refuse = next(c for c in broken["cases"] if c["expected_behavior"] == "refuse")
        refuse["reference_answer"] = "I do not know"
        refuse["required_points"] = [{"point_id": "x", "text": "x", "evidence": []}]
        problems = draft_lib.validate(broken, self.notes)
        self.assertTrue(any("refuse case with required points" in p for p in problems))
        self.assertTrue(any("exactly I don't know" in p for p in problems))

    def test_no_question_repeats_the_frozen_benchmark(self):
        import json
        from pathlib import Path
        frozen = {c["question"].strip().lower() for c in
                  json.loads(Path("evaluation/benchmarks/retrieval_v2.json").read_text(encoding="utf-8"))["cases"]}
        self.assertFalse(frozen & {c["question"].strip().lower() for c in self.draft["cases"]})


if __name__ == "__main__":
    unittest.main()
