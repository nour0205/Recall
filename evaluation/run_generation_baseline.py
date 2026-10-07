"""Controlled, unscored generation baseline. Run once from the repository root.

No application routes, planner, deduplication, fallback, reranker, or judge.
The output is exclusively created and checkpointed before/after each request;
an existing output is never overwritten or resumed automatically.
"""

import argparse
from datetime import datetime, timezone
import inspect
from importlib.metadata import version
import json
from pathlib import Path
from statistics import mean, median
import time

from app.orchestration.prompts import build_answer_prompt
from evaluation.benchmark import validate_corpus
from evaluation.generation_benchmark import (
    REFERENCE_PATH, RETRIEVAL_PATH, canonical_hash, file_hash,
    load_generation_benchmark, point_evidence,
)

OUTPUT_PATH = Path("evaluation/results/generation_baseline_v1.json")
TOP_K = 5
CANDIDATE_K = 10
RETRIEVAL_MODE = "hybrid"
FIXED_ROUTE = "unknown"  # Selects the unchanged generic branch; never planned.
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.0
MAX_TOKENS = 800
QUALITY_DIMENSIONS = ("correctness", "groundedness", "completeness", "refusal_correctness", "citation_correctness")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def prompt_version():
    return "build_answer_prompt:generic:sha256:" + canonical_hash(inspect.getsource(build_answer_prompt))


def configuration():
    return {
        "model": MODEL, "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
        "retrieval_mode": RETRIEVAL_MODE, "retrieval_algorithm": "Vector + BM25 + RRF",
        "top_k": TOP_K, "candidate_k": CANDIDATE_K, "rrf_k": 60,
        "fixed_route": FIXED_ROUTE, "prompt_version": prompt_version(),
        "automatic_retries": 0, "timeout_seconds": 60,
        "embedding_model": "text-embedding-3-small", "document_deduplication": False,
        "planner": False, "reranker": None, "application_fallbacks": False,
    }


def source_mapping(chunks):
    return {f"[S{i}]": {"chunk_id": chunk.chunk_id, "document_id": chunk.document_id,
                         "context_position": i} for i, chunk in enumerate(chunks, 1)}


def generate(client, question: str, chunks):
    """The model boundary accepts only a question and retrieved chunks.

No reference object, expected behavior, evidence labels, or rubric can be
passed through this interface. Capture exactly the messages submitted.
"""
    messages = build_answer_prompt(question=question, sources=chunks, route=FIXED_ROUTE)
    response = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
    )
    return messages, response


def safe_error(exc, stage):
    # Do not serialize exceptions containing request headers or credentials.
    return {"stage": stage, "type": type(exc).__name__,
            "status_code": getattr(exc, "status_code", None),
            "request_id": getattr(exc, "request_id", None)}


def run_case(case, reference, store, client, retrieve_fn, checkpoint, hashes):
    row = {
        "question_id": case.question_id, "question": case.question,
        "expected_behavior": reference.expected_behavior,
        "retrieved_context_chunks": [], "retrieved_chunk_ids": [], "source_mapping": {},
        "required_point_evidence": [], "context_sufficient_for_full_answer": None,
        "generated_answer": None, "model": MODEL, "response_model": None,
        "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
        "prompt_version": prompt_version(), "prompt_messages": None, "prompt_sha256": None,
        "retrieval_mode": RETRIEVAL_MODE, "retrieval_algorithm": "Vector + BM25 + RRF",
        "top_k": TOP_K, "candidate_k": CANDIDATE_K,
        "generation_latency_seconds": None, "retrieval_latency_seconds": None,
        "token_usage": None, "timestamp_utc": utc_now(), "completed_at_utc": None,
        "hashes": hashes, "response_id": None, "system_fingerprint": None,
        "finish_reason": None, "status": "retrieving", "error": None,
        "human_evaluation": {**dict.fromkeys(QUALITY_DIMENSIONS), "prompt_compliance": None},
    }
    checkpoint(row)
    started = time.perf_counter()
    try:
        chunks = retrieve_fn(store, case.question, mode=RETRIEVAL_MODE, k=TOP_K, candidate_k=CANDIDATE_K)
        if len(chunks) > TOP_K or len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("Invalid retrieved context size or duplicate chunk IDs")
        if any(not c.chunk_id or not c.document_id or not c.text for c in chunks):
            raise ValueError("Retrieved context missing stable identity or text")
        row["retrieved_context_chunks"] = [
            {**chunk.model_dump(mode="json"), "source_label": f"[S{i}]", "context_position": i}
            for i, chunk in enumerate(chunks, 1)
        ]
        row["retrieved_chunk_ids"] = [chunk.chunk_id for chunk in chunks]
        row["source_mapping"] = source_mapping(chunks)
        row["required_point_evidence"] = point_evidence(reference, case, chunks)
        factual = [p["sufficient_retrieved_evidence"] for p in row["required_point_evidence"]
                   if p["sufficient_retrieved_evidence"] is not None]
        row["context_sufficient_for_full_answer"] = all(factual) if factual else None
    except Exception as exc:
        row["status"] = "retrieval_failed"
        row["error"] = safe_error(exc, "retrieval")
        row["retrieval_latency_seconds"] = time.perf_counter() - started
        row["completed_at_utc"] = utc_now()
        checkpoint(row)
        return row
    row["retrieval_latency_seconds"] = time.perf_counter() - started
    row["prompt_messages"] = build_answer_prompt(question=case.question, sources=chunks, route=FIXED_ROUTE)
    row["prompt_sha256"] = canonical_hash(row["prompt_messages"])
    row["status"] = "generating"
    row["generation_started_at_utc"] = utc_now()
    checkpoint(row)  # Evidence and request persisted BEFORE the one API call.
    started = time.perf_counter()
    try:
        messages, response = generate(client, case.question, chunks)
        if messages != row["prompt_messages"]:
            raise ValueError("Prompt changed after checkpoint")
        row["generated_answer"] = response.choices[0].message.content
        row["response_id"] = response.id
        row["response_model"] = response.model
        row["system_fingerprint"] = response.system_fingerprint
        row["finish_reason"] = response.choices[0].finish_reason
        row["token_usage"] = response.usage.model_dump(mode="json") if response.usage else None
        row["status"] = "completed" if row["generated_answer"] else "empty_response"
    except Exception as exc:
        row["status"] = "generation_failed"
        row["error"] = safe_error(exc, "generation")
    row["generation_latency_seconds"] = time.perf_counter() - started
    row["completed_at_utc"] = utc_now()
    checkpoint(row)
    return row


def operational_summary(rows):
    successful = [r for r in rows if r["status"] == "completed"]
    latencies = [r["generation_latency_seconds"] for r in successful]
    usages = [r["token_usage"] for r in successful if r["token_usage"] is not None]
    return {
        "case_count": len(rows), "completed_generations": len(successful),
        "failures": [{"question_id": r["question_id"], "status": r["status"], "error": r["error"]}
                     for r in rows if r["status"] != "completed"],
        "generation_latency_seconds": {"count": len(latencies), "total": sum(latencies),
            "mean": mean(latencies) if latencies else None, "median": median(latencies) if latencies else None,
            "min": min(latencies) if latencies else None, "max": max(latencies) if latencies else None},
        "token_usage": {"available_case_count": len(usages), **{
            name: sum(u.get(name, 0) for u in usages) for name in ("prompt_tokens", "completion_tokens", "total_tokens")}},
        "insufficient_context_cases": [r["question_id"] for r in rows
                                        if r["context_sufficient_for_full_answer"] is False],
    }


def corpus_snapshot(store):
    """Hash logical corpus contents, not mutable database bytes."""
    from whoosh import index
    from app.vectordb.whoosh_index import INDEX_DIR

    records = store.collection.get(include=["documents", "metadatas"])
    chroma = sorted([
        {"chunk_id": cid, "document_id": metadata["document_id"], "text": text}
        for cid, text, metadata in zip(records["ids"], records["documents"], records["metadatas"])
    ], key=lambda row: row["chunk_id"])
    ix = index.open_dir(str(INDEX_DIR))  # Existing index only; no get-or-create.
    try:
        with ix.reader() as reader:
            whoosh = sorted(list(reader.all_stored_fields()), key=lambda row: row["chunk_id"])
    finally:
        ix.close()
    return {"chroma_text_sha256": canonical_hash(chroma), "whoosh_records_sha256": canonical_hash(whoosh),
            "chroma_records_sha256": canonical_hash(sorted([
                {"chunk_id": cid, "text": text, "metadata": metadata}
                for cid, text, metadata in zip(records["ids"], records["documents"], records["metadatas"])
            ], key=lambda row: row["chunk_id"]))}


def save_checkpoint(path, report):
    temporary = path.with_suffix(path.suffix + ".checkpoint")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def main(output_path=OUTPUT_PATH):
    output_path = Path(output_path)
    # Guard before credentials, network access, or loading live clients.
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite or rerun existing baseline: {output_path}")
    benchmark, references = load_generation_benchmark()
    from openai import OpenAI
    import chromadb
    from whoosh import index
    from app.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE as PROD_TEMP, MAX_TOKENS as PROD_MAX
    from app.embeddings import embedder
    from app.vectordb.chroma_store import ChromaStore
    from app.vectordb.whoosh_index import INDEX_DIR
    from evaluation.retrieval import retrieve
    from evaluation.run_retrieval_benchmark import corpus_inventories

    if (MODEL_NAME, PROD_TEMP, PROD_MAX) != (MODEL, TEMPERATURE, MAX_TOKENS):
        raise ValueError("Production generation parameters changed; review the frozen baseline")
    if not Path(".chroma/chroma.sqlite3").is_file() or not index.exists_in(str(INDEX_DIR)):
        raise ValueError("Baseline requires the existing persisted Chroma and Whoosh databases")
    chroma_client = chromadb.PersistentClient(path=".chroma")
    store = ChromaStore.__new__(ChromaStore)
    store.client = chroma_client
    store.collection = chroma_client.get_collection(benchmark.corpus.collection_name)
    inventories = corpus_inventories(store)
    for name, inventory in inventories.items():
        issues = validate_corpus(benchmark, {name: inventory})
        if issues:
            raise ValueError(f"Invalid {name} evidence inventory: {issues}")
    corpus_hashes = corpus_snapshot(store)
    if corpus_hashes["chroma_text_sha256"] != references.corpus["chroma_text_sha256"]:
        raise ValueError("Corpus texts changed since generation references were frozen")
    # Changes are confined to this evaluation process; production files untouched.
    embedder.client = embedder.client.with_options(max_retries=0, timeout=60)
    client = OpenAI(api_key=OPENAI_API_KEY, max_retries=0, timeout=60)
    hashes = {"retrieval_benchmark_sha256": file_hash(RETRIEVAL_PATH),
              "generation_reference_sha256": file_hash(REFERENCE_PATH), **corpus_hashes}
    report = {
        "result_schema_version": 1, "run_status": "running", "started_at_utc": utc_now(),
        "completed_at_utc": None, "configuration": configuration(), "hashes": hashes,
        "benchmark_path": RETRIEVAL_PATH.as_posix(), "reference_path": REFERENCE_PATH.as_posix(),
        "corpus": {"collection_name": benchmark.corpus.collection_name,
            "chunk_counts": {name: len(inv) for name, inv in inventories.items()},
            "validation_issues": validate_corpus(benchmark, inventories)},
        "runtime_versions": {name: version(name) for name in ("openai", "chromadb", "Whoosh", "pydantic")},
        "quality_scoring": "not_performed", "queries": [], "operational_summary": None,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive reservation prevents concurrent processes from duplicating requests.
    with output_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")

    def checkpoint(row):
        if report["queries"] and report["queries"][-1]["question_id"] == row["question_id"]:
            report["queries"][-1] = row
        else:
            report["queries"].append(row)
        save_checkpoint(output_path, report)

    try:
        for case, reference in zip(benchmark.cases, references.cases):
            row = run_case(case, reference, store, client, retrieve, checkpoint, hashes)
            print(f"{case.question_id}: {row['status']}; context_sufficient={row['context_sufficient_for_full_answer']}", flush=True)
        report["corpus_hashes_after"] = corpus_snapshot(store)
        report["corpus_unchanged"] = report["corpus_hashes_after"] == corpus_hashes
        report["run_status"] = "completed" if all(r["status"] == "completed" for r in report["queries"]) else "completed_with_failures"
        if not report["corpus_unchanged"]:
            report["run_status"] = "corpus_changed_during_run"
    except BaseException:
        report["run_status"] = "interrupted"
        raise
    finally:
        report["completed_at_utc"] = utc_now()
        report["operational_summary"] = operational_summary(report["queries"])
        save_checkpoint(output_path, report)
        client.close()
    print(json.dumps(report["operational_summary"], indent=2), flush=True)
    print(f"Raw baseline: {output_path}", flush=True)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    main(parser.parse_args().output)
