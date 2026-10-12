"""Demo notes and seed command; offline, no API key or indexes."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import re
import unittest

from app.ingestion.chunker import apply_overlap, base_chunks
from app import seed_demo

DEMO = Path('demo_notes')
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')


class DemoNotesTests(unittest.TestCase):
    def setUp(self):
        self.notes = seed_demo.load_manifest()

    def test_manifest_lists_every_note_file_exactly_once(self):
        files = sorted(p.name for p in DEMO.glob('*.txt'))
        self.assertEqual(sorted(n['file'] for n in self.notes), files)
        self.assertEqual(len({n['document_id'] for n in self.notes}), 12)

    def test_notes_chunk_like_the_benchmark_corpus(self):
        # Production ingestion settings; the benchmark corpus had 27 chunks.
        total = 0
        for note in self.notes:
            text = (DEMO / note['file']).read_text(encoding='utf-8').strip()
            chunks = apply_overlap(base_chunks(text), overlap=1)
            self.assertEqual(len(chunks), len(note['benchmark_chunk_ids']), note['document_id'])
            total += len(chunks)
        self.assertEqual(total, 27)

    def test_every_benchmark_chunk_maps_to_a_demo_note_position(self):
        known = {c for n in self.notes for c in n['benchmark_chunk_ids']}
        for name in ('retrieval_v1.json', 'retrieval_v2.json', 'generation_reference_v1.json'):
            text = (Path('evaluation/benchmarks') / name).read_text(encoding='utf-8')
            self.assertLessEqual(set(UUID.findall(text)), known, name)

    def test_seed_sends_each_note_through_ingestion(self):
        received = []

        def fake_ingest(request):
            received.append(request)
            return {'status': 'ingested', 'chunks_added': 1}

        with redirect_stdout(io.StringIO()):
            statuses = seed_demo.seed(ingest=fake_ingest)
        self.assertEqual(set(statuses.values()), {'ingested'})
        self.assertEqual([r.document_id for r in received], [n['document_id'] for n in self.notes])
        first, note = received[0], self.notes[0]
        self.assertEqual(first.text, (DEMO / note['file']).read_text(encoding='utf-8').strip())
        self.assertEqual((first.document_type, first.course, first.topic_tags, first.source),
                         ('lecture_note', note['course'], note['topic_tags'], note.get('source')))

    def test_seed_reports_duplicates_without_failing(self):
        with redirect_stdout(io.StringIO()):
            statuses = seed_demo.seed(ingest=lambda request: {'status': 'duplicate'})
        self.assertEqual(set(statuses.values()), {'duplicate'})


if __name__ == '__main__':
    unittest.main()
