"""The study hint names the notes an answer came from, in ranking order."""
from types import SimpleNamespace
import unittest

from app.orchestration.utils import build_study_hint


def source(document_id):
    return SimpleNamespace(document_id=document_id, text="passage")


class StudyHintTest(unittest.TestCase):
    def test_names_each_note_once_in_ranking_order(self):
        sources = [source("ml_overfitting"), source("db_normalization"), source("ml_overfitting")]
        self.assertEqual(build_study_hint(sources), "Review the relevant material in: ml_overfitting, db_normalization")

    def test_no_sources_no_hint(self):
        self.assertIsNone(build_study_hint([]))


if __name__ == "__main__":
    unittest.main()
