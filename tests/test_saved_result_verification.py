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
