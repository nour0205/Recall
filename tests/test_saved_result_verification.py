"""Historical inputs must reproduce scores; tampered provenance must fail."""
import json
from pathlib import Path
import tempfile
import unittest
from evaluation.verify_saved_results import REPORT, verify


class SavedResultVerificationTest(unittest.TestCase):
    def test_historical_results_reproduce(self):
        result = verify()
        self.assertEqual(result["answerable_count"], 16)
        self.assertEqual(result["aggregates"]["hybrid"]["evidence"]["mrr"], .96875)

    def test_modified_provenance_is_rejected(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        report["provenance"]["source_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                verify(path)


class JudgeAgreementVerificationTest(unittest.TestCase):
    def test_published_judge_agreement_reproduces(self):
        from evaluation.verify_saved_results import verify_judge_calibration
        table = verify_judge_calibration()
        self.assertEqual(table["judge_v2"]["completeness_points"], ("140/144", 0.82))
        self.assertEqual(table["judge_v2"]["correctness"], ("57/64", 0.75))
        self.assertEqual(table["judge_v2_vs_ragas"]["groundedness"], ("57/64", 0.73))
        self.assertEqual(table["ragas"]["faithfulness"], ("51/64", 0.58))

    def test_a_changed_judgment_is_rejected(self):
        from evaluation import verify_saved_results as verifier
        path, _ = verifier.JUDGE_CALIBRATIONS["judge_v2"]
        report = json.loads(path.read_text(encoding="utf-8"))
        row = next(r for r in report["judgments"] if r["human"]["correctness"] == 1 and r["judge"]["correctness"] == 1)
        row["judge"]["correctness"] = 0
        with tempfile.TemporaryDirectory() as directory:
            tampered = Path(directory) / path.name
            tampered.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "judge_v2 correctness"):
                verifier.verify_judge_calibration({"judge_v2": (tampered, verifier.JUDGE_CALIBRATIONS["judge_v2"][1])})
