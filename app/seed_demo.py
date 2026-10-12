"""Load the demo notes (demo_notes/) into Recall.

Usage, from the repository root:
    python -m app.seed_demo

Notes go through the same ingestion path as the API, so re-running is safe:
notes already in the library are reported as duplicates and skipped.
"""
import json
from pathlib import Path
from typing import Callable

from app.schemas.api import IngestRequest

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo_notes"


def load_manifest(demo_dir: Path = DEMO_DIR) -> list[dict]:
    manifest = json.loads((demo_dir / "manifest.json").read_text(encoding="utf-8"))
    return manifest["notes"]


def build_requests(demo_dir: Path = DEMO_DIR) -> list[IngestRequest]:
    requests = []
    for note in load_manifest(demo_dir):
        requests.append(
            IngestRequest(
                document_id=note["document_id"],
                # Strip the file's trailing newline; the UI sends trimmed text too.
                text=(demo_dir / note["file"]).read_text(encoding="utf-8").strip(),
                document_type="lecture_note",
                course=note.get("course"),
                topic_tags=note.get("topic_tags", []),
                source=note.get("source"),
            )
        )
    return requests


def seed(ingest: Callable[[IngestRequest], dict] | None = None, demo_dir: Path = DEMO_DIR) -> dict[str, str]:
    if ingest is None:
        # Imported lazily: it opens the indexes and needs OPENAI_API_KEY.
        from app.api.main import ingest

    statuses = {}
    for request in build_requests(demo_dir):
        result = ingest(request)
        statuses[request.document_id] = result.get("status", "unknown")
        detail = f" ({result['chunks_added']} chunks)" if "chunks_added" in result else ""
        print(f"{statuses[request.document_id]:>10}  {request.document_id}{detail}")

    counts = {status: list(statuses.values()).count(status) for status in sorted(set(statuses.values()))}
    print("\n" + ", ".join(f"{n} {SUMMARY.get(status, status)}" for status, n in counts.items()))
    return statuses


SUMMARY = {
    "ingested": "added",
    "duplicate": "already in the library",
    "conflict": "skipped (a note with that name already exists)",
}


if __name__ == "__main__":
    seed()
