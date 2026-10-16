"""RAGAS input building and calibration maths; offline, RAGAS not required."""
import unittest

from evaluation import ragas_data as rd
from evaluation import run_judge


class RagasDataTests(unittest.TestCase):
    def test_run_rows_skip_refusals_and_take_v3_references(self):
        rows, skipped = rd.rows_from_run(run_judge.RESULTS / "end_to_end_benchmark_v3_draft_20261013T143406Z.json")
        self.assertEqual(len(rows) + len(skipped), 48)
        self.assertEqual(len(skipped), 16)  # 14 correct refusals + 2 false refusals in that run
        first = rows[0]
        self.assertEqual(set(first) >= {"user_input", "retrieved_contexts", "response", "reference"}, True)
        self.assertTrue(all(row["retrieved_contexts"] for row in rows))
        self.assertNotIn("I don't know.", {row["response"].strip() for row in rows})

    def test_calibration_rows_carry_human_labels_and_skip_refusals(self):
        cases = run_judge.calibration_cases()
        rows, skipped = rd.rows_from_calibration(cases)
        self.assertEqual(len(rows) + len(skipped), 76)
        self.assertTrue(all("groundedness" in row["human"] for row in rows))
        self.assertEqual(len({row["question_id"] for row in rows}), len(rows))

    def test_auc(self):
        self.assertEqual(rd.auc([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]), 1.0)
        self.assertEqual(rd.auc([0.1, 0.2, 0.8, 0.9], [1, 1, 0, 0]), 0.0)
        self.assertEqual(rd.auc([0.5, 0.5], [1, 0]), 0.5)
        self.assertIsNone(rd.auc([0.5, 0.6], [1, 1]))

    def test_calibrate_reports_missed_failures(self):
        rows = [{"scores": {"faithfulness": s}, "human": {"groundedness": y}}
                for s, y in [(1.0, 1), (1.0, 0), (0.4, 0), (0.95, 1)]]
        report = rd.calibrate(rows, "faithfulness", "groundedness", thresholds=(1.0,))
        self.assertEqual(report["auc"], 0.625)  # (0.5 + 1 + 0 + 1) / 4 pairs
        strict = report["thresholds"][0]
        self.assertEqual((strict["agreement"], strict["missed_failures"], strict["false_alarms"]), ("2/4", 1, 1))


if __name__ == "__main__":
    unittest.main()
