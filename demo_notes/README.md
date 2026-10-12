# Demo notes

The 12 short lecture notes (machine learning, operating systems and databases) that Recall's evaluation benchmark was built on. Load them into an empty install with:

```sh
python -m app.seed_demo
```

Seeding goes through the normal ingestion path, so it calls the embedding API (a fraction of a cent) and is safe to re-run: notes already in the library are skipped.

## Provenance

The original benchmark corpus was only stored in local indexes. These files were recovered from those indexes, and re-ingesting them reproduces the original 27 chunks exactly (same text at every note and position). `tests/test_demo_notes.py` checks the chunk counts on every run. Ingestion collapses whitespace, so line breaks in some originals could not be recovered; everything Recall indexes is unchanged. The only metadata change is a typo fix in one topic tag.

`manifest.json` keeps each note's course, topic tags and `source` label. `source` is indexed by BM25, so it is preserved to keep keyword retrieval identical.

## Using the benchmark labels on a fresh install

The benchmark files in `evaluation/benchmarks/` identify evidence by chunk ID. A fresh install creates new IDs, so `benchmark_chunk_ids` in the manifest lists each note's original chunk IDs in order. Map a benchmark label to your install through its note and position: the label's chunk ID → its `document_id` and index in that list → the chunk with the same `document_id` and `chunk_index` in your install.
