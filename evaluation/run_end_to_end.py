"""End-to-end run of the production /ask path. Unscored.

Seeds a fresh, isolated workspace from demo_notes/, then sends every benchmark
question through the real FastAPI /ask endpoint: live hybrid retrieval and the
production prompt, with production settings and fallbacks. Thin wrappers
observe the retrieved context, prompt fingerprints and token usage without
changing behaviour. On commits that still have the intent planner, its output
is recorded too, and --no-planner skips it.

Answer quality is not judged here. Rows record only facts that need no
judgement: refusal behaviour, cited labels, and whether the retrieved context
contained the benchmark's required evidence. Run from the repository root:

    python -m evaluation.run_end_to_end

Each run writes a new timestamped file under evaluation/results/ and never
overwrites an existing one. It calls the OpenAI API (embeddings for seeding and
queries, then the answer model for each question).
"""

import argparse
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import shutil
from statistics import mean, median
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

from app.ingestion.chunker import apply_overlap, base_chunks
from app.orchestration.prompts import PROMPT_VERSION, REFUSAL
from app.seed_demo import DEMO_DIR, load_manifest
from evaluation.generation_benchmark import (
    REFERENCE_PATH, RETRIEVAL_PATH, canonical_hash, file_hash,
    load_generation_benchmark, point_evidence,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "evaluation" / "results"
PLANNER_BYPASS = {"route": "unknown", "targets": [], "reason": "planner disabled for this run"}
CITATION = re.compile(r"\[(S\d+(?:\s*,\s*S\d+)*)\]")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Pure helpers (tested offline)
# ---------------------------------------------------------------------------
def benchmark_chunk_map(notes) -> dict[tuple[str, int], str]:
    """(document_id, chunk position) -> chunk ID used by the benchmark labels."""
    return {(note["document_id"], position): chunk_id
            for note in notes for position, chunk_id in enumerate(note["benchmark_chunk_ids"])}


def expected_corpus(notes, demo_dir=DEMO_DIR) -> dict[tuple[str, int], str]:
    corpus = {}
    for note in notes:
        text = (demo_dir / note["file"]).read_text(encoding="utf-8").strip()
        for position, chunk in enumerate(apply_overlap(base_chunks(text), overlap=1)):
            corpus[(note["document_id"], position)] = chunk
    return corpus


def cited_labels(answer: str) -> list[int]:
    labels = set()
    for match in CITATION.finditer(answer or ""):
        labels.update(int(label.strip()[1:]) for label in match.group(1).split(","))
    return sorted(labels)


def refusal_outcome(expected_behavior: str, answer: str) -> str:
    refused = (answer or "").strip() == REFUSAL
    if expected_behavior == "refuse":
        return "correct_refusal" if refused else "missed_refusal"
    return "false_refusal" if refused else "answered"


def to_benchmark_chunks(chunks, chunk_map):
    """Give retrieved chunks the benchmark's chunk IDs so evidence groups apply."""
    mapped = []
    for chunk in chunks:
        position = chunk.get("chunk_index")
        key = (chunk.get("document_id"), int(position) if position is not None else None)
        mapped.append(SimpleNamespace(document_id=key[0], chunk_id=chunk_map.get(key)))
    return mapped


def quote_evidence(required_points, retrieved) -> list[dict]:
    """v3 benchmark: a point has evidence when any of its quotes appears in a retrieved chunk."""
    texts = [(c.get("document_id"), c.get("text") or "") for c in retrieved or []]
    output = []
    for point in required_points:
        found = sorted({doc for e in point["evidence"] for doc, text in texts
                        if doc == e["document_id"] and e["quote"] in text})
        output.append({"point_id": point["point_id"], "sufficient_retrieved_evidence": bool(found),
                       "documents_with_evidence": found, "method": "verbatim_quote_in_retrieved_chunk"})
    return output


def load_v3_cases(path: Path):
    """Adapt the quote-based v3 benchmark to the runner's (case, reference) pairs."""
    draft = json.loads(Path(path).read_text(encoding="utf-8"))
    pairs = []
    for raw in draft["cases"]:
        case = SimpleNamespace(question_id=raw["question_id"], question=raw["question"], category=raw["category"])
        reference = SimpleNamespace(expected_behavior=raw["expected_behavior"], required_points=raw["required_points"])
        pairs.append((case, reference))
    return pairs


def build_row(case, reference, *, status_code, response, plan, retrieved, calls, latency, chunk_map, evidence=None):
    answer = (response or {}).get("answer")
    sources = (response or {}).get("sources") or []
    if evidence is None:
        evidence = point_evidence(reference, case, to_benchmark_chunks(retrieved or [], chunk_map))
    factual = [p["sufficient_retrieved_evidence"] for p in evidence if p["sufficient_retrieved_evidence"] is not None]
    labels = cited_labels(answer)
    answer_calls = [c for c in calls if c["kind"] == "chat" and c["stage"] == "answer"]
    return {
        "question_id": case.question_id,
        "question": case.question,
        "category": getattr(case, "category", None),
        "expected_behavior": reference.expected_behavior,
        "http_status": status_code,
        "answer": answer,
        "refusal_outcome": refusal_outcome(reference.expected_behavior, answer) if answer is not None else None,
        "route": (response or {}).get("route"),
        "planner": plan,
        "study_hint": (response or {}).get("study_hint"),
        "retrieved_context": retrieved,
        "sources": sources,
        "cited_labels": labels,
        "invalid_cited_labels": [n for n in labels if not 1 <= n <= len(sources)],
        "required_point_evidence": evidence,
        "context_sufficient_for_full_answer": all(factual) if factual else None,
        "latency_seconds": latency,
        "model_calls": calls,
        # One answer call per request; a second one means the fallback ran.
        "fallback_suspected": len(answer_calls) > 1,
        "completed_at_utc": utc_now(),
    }


def _stats(values):
    if not values:
        return None
    ordered = sorted(values)
    return {"count": len(ordered), "mean": mean(ordered), "median": median(ordered),
            "p90": ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))], "max": ordered[-1]}


def summarize(rows) -> dict:
    ok = [r for r in rows if r["http_status"] == 200]
    answerable = [r for r in ok if r["expected_behavior"] == "answer"]
    refuse = [r for r in ok if r["expected_behavior"] == "refuse"]
    outcomes = {}
    for r in ok:
        outcomes[r["refusal_outcome"]] = outcomes.get(r["refusal_outcome"], 0) + 1
    routes = {}
    for r in ok:
        routes[r["route"]] = routes.get(r["route"], 0) + 1

    def tokens(kind, stage=None):
        calls = [c for r in ok for c in r["model_calls"] if c["kind"] == kind and (stage is None or c["stage"] == stage)]
        return {name: sum((c["usage"] or {}).get(name, 0) for c in calls)
                for name in ("prompt_tokens", "completion_tokens", "total_tokens")} | {"calls": len(calls)}

    answered = [r for r in answerable if r["refusal_outcome"] == "answered"]
    return {
        "cases": len(rows),
        "http_ok": len(ok),
        "errors": [{"question_id": r["question_id"], "http_status": r["http_status"]} for r in rows if r["http_status"] != 200],
        "refusal_outcomes": outcomes,
        "expected_refusals_refused": f"{outcomes.get('correct_refusal', 0)}/{len(refuse)}",
        "answerable_falsely_refused": f"{outcomes.get('false_refusal', 0)}/{len(answerable)}",
        "answerable_with_all_required_evidence_retrieved": (
            f"{sum(r['context_sufficient_for_full_answer'] is True for r in answerable)}/{len(answerable)}"),
        "false_refusals_with_evidence_retrieved": [r["question_id"] for r in answerable
                                                   if r["refusal_outcome"] == "false_refusal"
                                                   and r["context_sufficient_for_full_answer"]],
        "answers_with_citations": f"{sum(bool(r['cited_labels']) for r in answered)}/{len(answered)}",
        "answers_with_invalid_citations": [r["question_id"] for r in ok if r["invalid_cited_labels"]],
        "planner_routes": routes,
        "planner_scoped_cases": [r["question_id"] for r in ok if (r["planner"] or {}).get("targets")],
        "fallback_suspected": [r["question_id"] for r in ok if r["fallback_suspected"]],
        "latency_seconds": _stats([r["latency_seconds"] for r in ok]),
        "tokens": {"planner": tokens("chat", "planner"), "answer": tokens("chat", "answer"),
                   "query_embeddings": tokens("embedding")},
        "by_category": _by_category(ok),
    }


def _by_category(rows) -> dict | None:
    if not any(r.get("category") for r in rows):
        return None
    result = {}
    for category in sorted({r["category"] for r in rows}):
        group = [r for r in rows if r["category"] == category]
        answerable = [r for r in group if r["expected_behavior"] == "answer"]
        result[category] = {
            "cases": len(group),
            "refusal_outcomes": {o: sum(r["refusal_outcome"] == o for r in group)
                                 for o in sorted({r["refusal_outcome"] for r in group})},
            "evidence_retrieved": (f"{sum(r['context_sufficient_for_full_answer'] is True for r in answerable)}/{len(answerable)}"
                                   if answerable else None),
        }
    return result


# ---------------------------------------------------------------------------
# Live run
# ---------------------------------------------------------------------------
class CallRecorder:
    """Records usage of every model call made through the app's OpenAI clients."""

    def __init__(self):
        self.calls = []
        self.stage = None

    def wrap(self, kind, create):
        def recorded(*args, **kwargs):
            started = time.perf_counter()
            response = create(*args, **kwargs)
            usage = getattr(response, "usage", None)
            self.calls.append({"kind": kind, "stage": self.stage if kind == "chat" else "query",
                               "model": getattr(response, "model", None),
                               "messages_sha256": canonical_hash(kwargs["messages"]) if "messages" in kwargs else None,
                               "latency_seconds": time.perf_counter() - started,
                               "usage": usage.model_dump(mode="json") if usage else None})
            return response
        return recorded

    def take(self):
        calls, self.calls = self.calls, []
        return calls


@contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def git_commit():
    head = REPO_ROOT / ".git" / "HEAD"
    try:
        ref = head.read_text(encoding="utf-8").strip()
        if ref.startswith("ref: "):
            return (REPO_ROOT / ".git" / ref[5:]).read_text(encoding="utf-8").strip()
        return ref
    except OSError:
        return None


def save(path: Path, report: dict):
    temporary = path.with_suffix(path.suffix + ".checkpoint")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def main(output_path: Path | None = None, keep_workspace: bool = False, planner: bool = True, benchmark_path: Path | None = None):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"end_to_end_v1_{stamp}.json" if planner else f"end_to_end_v1_no_planner_{stamp}.json"
    if benchmark_path:
        name = f"end_to_end_{Path(benchmark_path).stem}_{stamp}.json"
    output_path = Path(output_path or RESULTS_DIR / name).resolve()
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite an existing run: {output_path}")

    if benchmark_path:
        pairs = load_v3_cases(REPO_ROOT / benchmark_path)
    else:
        benchmark, references = load_generation_benchmark(REPO_ROOT / REFERENCE_PATH, REPO_ROOT / RETRIEVAL_PATH)
        pairs = list(zip(benchmark.cases, references.cases))
    notes = load_manifest()
    chunk_map = benchmark_chunk_map(notes)
    workspace = Path(tempfile.mkdtemp(prefix="recall-e2e-"))

    report = {
        "result_schema_version": 1,
        "run_status": "running",
        "started_at_utc": utc_now(),
        "completed_at_utc": None,
        "description": "Production /ask on a fresh install seeded from demo_notes/. Unscored.",
        "configuration": {"endpoint": "POST /ask", "prompt_version": PROMPT_VERSION,
                          "planner": planner, "fallbacks": "production", "sdk_retries": "production defaults"},
        "provenance": {
            "git_commit": git_commit(),
            "benchmark": Path(benchmark_path).as_posix() if benchmark_path else RETRIEVAL_PATH.as_posix(),
            "benchmark_sha256": file_hash(REPO_ROOT / (benchmark_path or RETRIEVAL_PATH)),
            "generation_reference_sha256": None if benchmark_path else file_hash(REPO_ROOT / REFERENCE_PATH),
            "demo_manifest_sha256": file_hash(DEMO_DIR / "manifest.json"),
            "runtime_versions": {name: version(name) for name in ("openai", "chromadb", "Whoosh", "fastapi")},
        },
        "corpus": None,
        "queries": [],
        "summary": None,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)

    recorder = CallRecorder()
    try:
        with working_directory(workspace):
            # Imported here so the app's relative index paths resolve inside the workspace.
            from fastapi.testclient import TestClient
            from app.api import main as api
            from app.config import MODEL_NAME, TEMPERATURE, MAX_TOKENS
            from app.embeddings import embedder
            from app.llm import client as llm
            from app.seed_demo import seed

            # /ask has no planner since the planner ablation; older commits still do.
            has_planner = hasattr(api, "plan_question")
            report["configuration"].update({"model": MODEL_NAME, "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
                                            "planner": planner and has_planner, "app_has_planner": has_planner})
            llm.client.chat.completions.create = recorder.wrap("chat", llm.client.chat.completions.create)
            embedder.client.embeddings.create = recorder.wrap("embedding", embedder.client.embeddings.create)

            recorder.stage = "seed"
            statuses = seed(ingest=api.ingest)
            seed_calls = recorder.take()
            stored = api.store.collection.get(include=["documents", "metadatas"])
            corpus = {(m["document_id"], int(m["chunk_index"])): text
                      for text, m in zip(stored["documents"], stored["metadatas"])}
            report["corpus"] = {
                "seed_statuses": statuses,
                "chunks": len(corpus),
                "matches_demo_notes": corpus == expected_corpus(notes),
                "text_sha256": canonical_hash(sorted([d, p, t] for (d, p), t in corpus.items())),
                "seed_embedding_tokens": sum((c["usage"] or {}).get("total_tokens", 0) for c in seed_calls),
            }
            if not report["corpus"]["matches_demo_notes"]:
                raise RuntimeError("Seeded corpus does not match demo_notes/; aborting before any question")
            save(output_path, report)

            observed = {}

            def observe_plan(question):
                recorder.stage = "planner"
                # Bypass: the route the planner returned for most questions, with no model call.
                observed["plan"] = api_plan(question) if planner else dict(PLANNER_BYPASS)
                recorder.stage = "answer"
                return observed["plan"]

            def observe_retrieval(*args, **kwargs):
                results = api_retrieve(*args, **kwargs)
                observed.setdefault("retrieved", [
                    {"document_id": r.document_id, "chunk_index": r.chunk_index,
                     "hybrid_score": r.hybrid_score, "text": r.text} for r in results])
                return results

            api_plan, api_retrieve = getattr(api, "plan_question", None), api.hybrid_retrieve
            with ExitStack() as stack:
                if has_planner:
                    stack.enter_context(patch.object(api, "plan_question", observe_plan))
                stack.enter_context(patch.object(api, "hybrid_retrieve", observe_retrieval))
                http = stack.enter_context(TestClient(api.app))
                for case, reference in pairs:
                    observed.clear()
                    recorder.take()
                    recorder.stage = "answer"
                    started = time.perf_counter()
                    response = http.post("/ask", json={"question": case.question})
                    latency = time.perf_counter() - started
                    row = build_row(
                        case, reference, status_code=response.status_code,
                        response=response.json() if response.status_code == 200 else None,
                        plan=observed.get("plan"), retrieved=observed.get("retrieved"),
                        calls=recorder.take(), latency=latency, chunk_map=chunk_map,
                        evidence=quote_evidence(reference.required_points, observed.get("retrieved")) if benchmark_path else None)
                    report["queries"].append(row)
                    save(output_path, report)
                    print(f"{case.question_id}: {row['refusal_outcome']} "
                          f"(evidence retrieved: {row['context_sufficient_for_full_answer']})", flush=True)
        report["run_status"] = "completed" if all(r["http_status"] == 200 for r in report["queries"]) else "completed_with_errors"
    except BaseException:
        report["run_status"] = "interrupted"
        raise
    finally:
        report["completed_at_utc"] = utc_now()
        report["summary"] = summarize(report["queries"])
        save(output_path, report)
        if not keep_workspace:
            shutil.rmtree(workspace, ignore_errors=True)
    print(json.dumps(report["summary"], indent=2), flush=True)
    print(f"Saved: {output_path}", flush=True)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, help="Result path (default: a new timestamped file)")
    parser.add_argument("--keep-workspace", action="store_true", help="Keep the temporary seeded install")
    parser.add_argument("--no-planner", action="store_true", help="Skip the planner call (route 'unknown', no targets)")
    parser.add_argument("--benchmark", type=Path, help="A quote-based benchmark such as evaluation/drafts/benchmark_v3_draft.json")
    args = parser.parse_args()
    main(args.output, args.keep_workspace, planner=not args.no_planner, benchmark_path=args.benchmark)
