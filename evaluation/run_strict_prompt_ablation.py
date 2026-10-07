"""One unscored strict-prompt run using only the frozen baseline contexts.

No retrieval, embeddings, corpus databases, planner, fallback, reranker, or judge
are imported or called. Model parameters and SDK options come from the baseline.
The sole experimental treatment is the saved evaluation-only prompt definition.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
from statistics import mean, median
import time

from evaluation.generation_benchmark import (
    CASE_IDS, REFERENCE_PATH, RETRIEVAL_PATH, canonical_hash, file_hash,
)
from evaluation.generation_human_review import BASELINE_PATH, LABEL_FIELDS, frozen_inputs

PROMPT_PATH = Path("evaluation/prompts/grounded_strict_v1.json")
PROMPT_VERSION = "grounded_strict_v1"
OUTPUT_PATH = Path("evaluation/results/generation_strict_prompt_v1.json")
CONTEXT_FIELDS = ("retrieved_context_chunks", "retrieved_chunk_ids", "source_mapping",
                  "required_point_evidence", "context_sufficient_for_full_answer")
QUALITY_FIELDS = (*LABEL_FIELDS, "completeness")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_prompt(path=PROMPT_PATH, expected_version=PROMPT_VERSION):
    prompt = json.loads(Path(path).read_text(encoding="utf-8"))
    if prompt.get("schema_version") != 1 or prompt.get("prompt_version") != expected_version:
        raise ValueError("Expected the frozen grounded_strict_v1 prompt definition")
    if set(prompt) != {"schema_version", "prompt_version", "system", "user_template"}:
        raise ValueError("Unexpected strict prompt fields")
    if not isinstance(prompt["system"], str) or "I don't know.\nStop immediately after this sentence." not in prompt["system"]:
        raise ValueError("Strict prompt must preserve the exact refusal instruction")
    if prompt["user_template"].count("{context}") != 1 or prompt["user_template"].count("{question}") != 1:
        raise ValueError("Strict user template must contain one context and question slot")
    return prompt


def context_block(context_chunks):
    # Same source serialization as the baseline's production prompt, without
    # importing production prompts or any retrieval code.
    return "\n\n".join(f"{chunk['source_label']} DOCUMENT: {chunk['document_id']}\nCONTENT:\n{chunk['text']}"
                       for chunk in context_chunks)


def build_strict_messages(question, context_chunks, prompt):
    """Narrow model boundary: no references, expected behavior, or scoring labels."""
    user = prompt["user_template"].format(context=context_block(context_chunks), question=question)
    return [{"role": "system", "content": prompt["system"]}, {"role": "user", "content": user}]


def request_parameters(configuration):
    return {field: configuration[field] for field in ("model", "temperature", "max_tokens")}


def validate_frozen_baseline(baseline):
    if tuple(row["question_id"] for row in baseline["queries"]) != CASE_IDS:
        raise ValueError("Frozen question ordering changed")
    cfg = baseline["configuration"]
    required = {"model": "gpt-4o-mini", "temperature": 0.0, "max_tokens": 800,
                "retrieval_mode": "hybrid", "retrieval_algorithm": "Vector + BM25 + RRF",
                "top_k": 5, "candidate_k": 10, "rrf_k": 60,
                "automatic_retries": 0, "timeout_seconds": 60,
                "planner": False, "reranker": None, "application_fallbacks": False}
    if any(cfg.get(key) != value for key, value in required.items()):
        raise ValueError("Frozen baseline configuration does not match the approved ablation")
    for row in baseline["queries"]:
        if request_parameters(row) != request_parameters(cfg):
            raise ValueError("Per-case generation settings differ from the frozen configuration")
        chunks = row["retrieved_context_chunks"]
        if len(chunks) != 5 or row["retrieved_chunk_ids"] != [chunk["chunk_id"] for chunk in chunks]:
            raise ValueError("Frozen source count/identity mismatch")
        mapping = {f"[S{i}]": {"chunk_id": chunk["chunk_id"], "document_id": chunk["document_id"], "context_position": i}
                   for i, chunk in enumerate(chunks, 1)}
        if row["source_mapping"] != mapping:
            raise ValueError("Frozen source mapping mismatch")
        for i, chunk in enumerate(chunks, 1):
            if chunk["source_label"] != f"[S{i}]" or chunk["context_position"] != i:
                raise ValueError("Frozen source order mismatch")
        exact = "Context:\n" + context_block(chunks) + "\n\nQuestion:\n" + row["question"] + "\n\n"
        if exact.encode("utf-8") not in row["prompt_messages"][1]["content"].encode("utf-8"):
            raise ValueError("Reused context bytes differ from the baseline prompt")


def protected_hashes():
    paths = {BASELINE_PATH, REFERENCE_PATH, RETRIEVAL_PATH, PROMPT_PATH,
             Path("evaluation/results/generation_baseline_v1_human_review.json"),
             Path("evaluation/results/generation_baseline_v1_summary.json"),
             Path("evaluation/results/generation_baseline_v1_summary.md")}
    paths.update(Path("app").rglob("*.py"))
    return {path.as_posix(): file_hash(path) for path in sorted(paths) if path.is_file()}


def save_checkpoint(path, report):
    temporary = path.with_suffix(path.suffix + ".checkpoint")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_case(baseline_row, client, prompt, configuration, hashes, checkpoint):
    row = {
        "question_id": baseline_row["question_id"], "question": baseline_row["question"],
        "expected_behavior": baseline_row["expected_behavior"],
        **{field: deepcopy(baseline_row[field]) for field in CONTEXT_FIELDS},
        **request_parameters(configuration), "response_model": None,
        "prompt_version": prompt["prompt_version"], "prompt_definition_sha256": hashes.get("prompt_definition_sha256", hashes.get("strict_prompt_definition_sha256")),
        "retrieval_mode": baseline_row["retrieval_mode"], "retrieval_algorithm": baseline_row["retrieval_algorithm"],
        "top_k": baseline_row["top_k"], "candidate_k": baseline_row["candidate_k"],
        "retrieval_executed": False, "context_origin": "generation_baseline_v1.json",
        "context_structural_sha256": canonical_hash(baseline_row["retrieved_context_chunks"]),
        "context_prompt_bytes_sha256": hashlib.sha256(context_block(baseline_row["retrieved_context_chunks"]).encode("utf-8")).hexdigest(),
        "source_mapping_sha256": canonical_hash(baseline_row["source_mapping"]),
        "generated_answer": None, "status": "generating", "error": None,
        "generation_latency_seconds": None, "token_usage": None, "response_id": None,
        "system_fingerprint": None, "finish_reason": None,
        "timestamp_utc": utc_now(), "completed_at_utc": None, "hashes": deepcopy(hashes),
        "human_evaluation": dict.fromkeys(QUALITY_FIELDS),
    }
    # Metadata above stays outside the model boundary.
    row["prompt_messages"] = build_strict_messages(row["question"], row["retrieved_context_chunks"], prompt)
    row["prompt_sha256"] = canonical_hash(row["prompt_messages"])
    checkpoint(row)  # Persist source order, exact messages, and settings before the one request.
    started = time.perf_counter()
    try:
        response = client.chat.completions.create(messages=row["prompt_messages"], **request_parameters(configuration))
        row["generated_answer"] = response.choices[0].message.content
        row["response_model"] = response.model
        row["response_id"] = response.id
        row["system_fingerprint"] = response.system_fingerprint
        row["finish_reason"] = response.choices[0].finish_reason
        row["token_usage"] = response.usage.model_dump(mode="json") if response.usage else None
        row["status"] = "completed" if row["generated_answer"] else "empty_response"
    except Exception as exc:
        row["status"] = "generation_failed"
        row["error"] = {"stage": "generation", "type": type(exc).__name__,
                        "status_code": getattr(exc, "status_code", None), "request_id": getattr(exc, "request_id", None)}
    row["generation_latency_seconds"] = time.perf_counter() - started
    row["completed_at_utc"] = utc_now()
    checkpoint(row)
    return row


def operational_summary(rows, baseline_rows):
    complete = [row for row in rows if row["status"] == "completed"]
    latency = [row["generation_latency_seconds"] for row in complete]
    usages = [row["token_usage"] for row in complete if row["token_usage"] is not None]
    baseline = {row["question_id"]: row for row in baseline_rows}
    paired_old = [baseline[row["question_id"]]["generated_answer"] for row in complete]
    paired_new = [row["generated_answer"] for row in complete]
    def lengths(answers):
        return {"mean_characters": mean(len(answer) for answer in answers) if answers else None,
                "mean_whitespace_words": mean(len(answer.split()) for answer in answers) if answers else None}
    old, new = lengths(paired_old), lengths(paired_new)
    return {
        "case_count": len(rows), "completed_generations": len(complete),
        "failures": [{"question_id": row["question_id"], "status": row["status"], "error": row["error"]}
                     for row in rows if row["status"] != "completed"],
        "generation_latency_seconds": {"count": len(latency), "total": sum(latency),
            "mean": mean(latency) if latency else None, "median": median(latency) if latency else None,
            "min": min(latency) if latency else None, "max": max(latency) if latency else None},
        "token_usage": {"available_case_count": len(usages), **{
            field: sum(usage.get(field, 0) for usage in usages) for field in ("prompt_tokens", "completion_tokens", "total_tokens")}},
        "answer_length_comparison": {
            "paired_case_count": len(complete), "baseline": old, "grounded_strict_v1": new,
            "strict_to_baseline_character_ratio": new["mean_characters"] / old["mean_characters"]
                if old["mean_characters"] else None,
            "method": "Unicode character count and whitespace split count; includes Markdown/citation text, excludes failed cases from both sides. Length is an operational comparison, not answer-quality scoring.",
        },
    }


def make_client(**options):
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key, **options)


def main(output_path=OUTPUT_PATH, client_factory=None, *, prompt_path=PROMPT_PATH,
         prompt_version=PROMPT_VERSION, protect=None, summarize=None):
    output_path = Path(output_path)
    if output_path.exists():
        raise FileExistsError("Refusing to overwrite or rerun an existing prompt ablation")
    _, _, baseline = frozen_inputs()  # File-only validation; no production imports or corpus access.
    validate_frozen_baseline(baseline)
    if version("openai") != baseline["runtime_versions"]["openai"]:
        raise ValueError("OpenAI SDK version differs from baseline; preserve request defaults")
    prompt_path = Path(prompt_path)
    prompt = load_prompt(prompt_path, prompt_version)
    protect = protect or protected_hashes
    summarize = summarize or operational_summary
    before = protect()
    configuration = {**deepcopy(baseline["configuration"]), "prompt_version": prompt_version}
    hashes = {**deepcopy(baseline["hashes"]), "frozen_baseline_sha256": file_hash(BASELINE_PATH),
              "strict_prompt_definition_sha256": file_hash(PROMPT_PATH)}
    if prompt_version != PROMPT_VERSION:
        hashes["prompt_definition_sha256"] = file_hash(prompt_path)
    factory = client_factory if client_factory is not None else make_client
    client = factory(max_retries=configuration["automatic_retries"], timeout=configuration["timeout_seconds"])
    report = {
        "result_schema_version": 1, "run_status": "running", "started_at_utc": utc_now(), "completed_at_utc": None,
        "configuration": configuration, "baseline_configuration": deepcopy(baseline["configuration"]),
        "experimental_change": f"Prompt only: {prompt_version}; questions, frozen contexts, source order, settings, and rubric are unchanged.",
        "prompt_definition": deepcopy(prompt), "prompt_definition_path": prompt_path.as_posix(),
        "baseline_path": BASELINE_PATH.as_posix(), "benchmark_path": RETRIEVAL_PATH.as_posix(),
        "reference_path": REFERENCE_PATH.as_posix(), "hashes": hashes,
        "protected_file_hashes_before": before, "protected_file_hashes_after": None,
        "protected_files_unchanged": None, "retrieval_executed": False, "embedding_calls": 0,
        "runtime_versions": {"openai": version("openai")},
        "corpus": deepcopy(baseline["corpus"]), "quality_scoring": "not_performed",
        "queries": [], "operational_summary": None,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    def checkpoint(row):
        if report["queries"] and report["queries"][-1]["question_id"] == row["question_id"]:
            report["queries"][-1] = row
        else:
            report["queries"].append(row)
        save_checkpoint(output_path, report)
    try:
        for original in baseline["queries"]:
            row = run_case(original, client, prompt, configuration, hashes, checkpoint)
            print(f"{row['question_id']}: {row['status']}", flush=True)
        report["run_status"] = "completed" if all(row["status"] == "completed" for row in report["queries"]) else "completed_with_failures"
    except BaseException:
        report["run_status"] = "interrupted"
        raise
    finally:
        report["completed_at_utc"] = utc_now()
        report["protected_file_hashes_after"] = protect()
        report["protected_files_unchanged"] = report["protected_file_hashes_after"] == before
        if not report["protected_files_unchanged"]:
            report["run_status"] = "protected_inputs_changed_during_run"
        report["operational_summary"] = summarize(report["queries"], baseline["queries"])
        save_checkpoint(output_path, report)
        client.close()
    print(json.dumps(report["operational_summary"], indent=2), flush=True)
    print(f"Unscored strict-prompt outputs: {output_path}", flush=True)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    main(parser.parse_args().output)
