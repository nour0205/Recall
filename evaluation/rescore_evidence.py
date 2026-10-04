"""Rescore saved top-five rankings without importing retrieval or reranking.

Run from repository root: python -m evaluation.rescore_evidence
RR/MRR use the saved final top five, exactly as the source experiment did.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import mean

from evaluation.benchmark import load_benchmark, validate_corpus
from evaluation.evidence_metrics import evidence_hit_at_k, evidence_recall_at_k, evidence_reciprocal_rank
from evaluation.metrics import hit_at_k, recall_at_k, reciprocal_rank

BENCHMARK = Path("evaluation/benchmarks/retrieval_v2.json")
SOURCE = Path("evaluation/results/semantic_ablation_20261004T092737920669Z.json")
MODES = ("hybrid", "hybrid_reranked", "hybrid_semantic_reranked")


def score(ids, groups):
    result = {}
    for k in (1, 3, 5):
        result[f"hit_at_{k}"] = evidence_hit_at_k(ids, groups, k)
        coverage = evidence_recall_at_k(ids, groups, k)
        result[f"recall_at_{k}"] = coverage
        result[f"complete_at_{k}"] = None if coverage is None else float(coverage == 1)
    result["reciprocal_rank"] = evidence_reciprocal_rank(ids, groups)
    return result


def rescore(benchmark, saved):
    source_cases = {q["question_id"]: q for q in saved["queries"]}
    if len(source_cases) != len(saved["queries"]) or set(source_cases) != {c.question_id for c in benchmark.cases}:
        raise ValueError("Saved question IDs must match benchmark exactly")
    if saved["configuration"]["k"] != 5 or saved["configuration"]["candidate_k"] != 10:
        raise ValueError("Expected source settings k=5 and candidate_k=10")
    rows = []
    for case in benchmark.cases:
        old = source_cases[case.question_id]
        canonical_ids = [c.chunk_id for c in case.relevant_chunks]
        if (old["question"] != case.question or old["answerable"] != case.answerable
                or set(old["relevant_chunk_ids"]) != set(canonical_ids)):
            raise ValueError(f"Source case does not match legacy labels: {case.question_id}")
        groups = [{c.chunk_id for c in g.acceptable_chunks} for g in case.evidence_groups]
        row = {"question_id": case.question_id, "question": case.question, "answerable": case.answerable,
               "notes": case.notes, "evidence_groups": [g.model_dump() for g in case.evidence_groups], "modes": {}}
        for mode in MODES:
            ids = old[mode]["retrieved_chunk_ids"]
            if len(ids) > 5:
                raise ValueError("Expected saved final top-five outputs")
            canonical = {f"{metric}_at_{k}": fn(ids, canonical_ids, k)
                         for metric, fn in (("hit", hit_at_k), ("recall", recall_at_k)) for k in (1,3,5)}
            canonical["reciprocal_rank"] = reciprocal_rank(ids, canonical_ids)
            if canonical != old[mode]["metrics"]:
                raise ValueError(f"Canonical source scores differ: {case.question_id}/{mode}")
            evidence = score(ids, groups)
            row["modes"][mode] = {"retrieved_chunk_ids": ids, "canonical": canonical, "evidence": evidence,
                "changed_metrics": [key for key in canonical if canonical[key] != evidence[key]],
                "first_group_ranks": [{"group_id": group.group_id,
                    "rank": next((rank for rank, cid in enumerate(ids,1) if cid in acceptable), None)}
                    for group, acceptable in zip(case.evidence_groups, groups)]}
        rows.append(row)
    aggregates = {}
    answerable = [q for q in rows if q["answerable"]]
    for mode in MODES:
        aggregates[mode] = {}
        for kind in ("canonical", "evidence"):
            keys = next(q for q in rows if q["answerable"])["modes"][mode][kind]
            aggregates[mode][kind] = {"mrr" if key == "reciprocal_rank" else key:
                mean(q["modes"][mode][kind][key] for q in answerable) for key in keys}
    return {"answerable_count": len(answerable), "queries": rows, "aggregates": aggregates}


def markdown(report):
    lines = ["# Evidence-group rescoring", "", "No retrieval or reranking was rerun. All scores use saved final top-five rankings.",
             "OR within groups; complete coverage requires all groups. Aggregates include only 16 answerable cases.",
             "Partial/background evidence counts only when it fully supplies a named group. Canonical and evidence scores are separate.",
             "", "## Provenance", "", "```json", json.dumps(report["provenance"],indent=2), "```",
             "", "## Aggregate metrics", "", "```json", json.dumps(report["aggregates"],indent=2), "```"]
    for q in report["queries"]:
        lines += ["", f"## {q['question_id']}: {q['question']}", "", f"Answerable: {q['answerable']}",
                  "", "```json", json.dumps(q["evidence_groups"],indent=2), "```",
                  "", "| Mode | Scoring | Hit 1/3/5 | Recall 1/3/5 | RR | Complete 1/3/5 |", "|---|---|---|---|---|---|"]
        for mode, row in q["modes"].items():
            for kind in ("canonical","evidence"):
                m=row[kind]
                hit=" / ".join(str(m[f"hit_at_{k}"]) for k in (1,3,5))
                recall=" / ".join(str(m[f"recall_at_{k}"]) for k in (1,3,5))
                complete=" / ".join(str(m[f"complete_at_{k}"]) for k in (1,3,5)) if kind=="evidence" else "—"
                lines.append(f"| {mode} | {kind} | {hit} | {recall} | {m['reciprocal_rank']} | {complete} |")
        for mode,row in q["modes"].items():
            lines += ["", f"**{mode}**", f"Ranked UUIDs: {json.dumps(row['retrieved_chunk_ids'])}",
                      f"First group ranks: {json.dumps(row['first_group_ranks'])}",
                      f"Changed metrics: {json.dumps(row['changed_metrics'])}"]
    return "\n".join(lines)+"\n"


def main():
    benchmark = load_benchmark(BENCHMARK)
    source_bytes = SOURCE.read_bytes()
    saved = json.loads(source_bytes)
    # Read persisted corpus solely to validate IDs/ownership, never to search it.
    import chromadb
    collection = chromadb.PersistentClient(path=".chroma").get_collection(benchmark.corpus.collection_name)
    corpus = collection.get(include=["metadatas"])
    inventory = {cid: meta["document_id"] for cid,meta in zip(corpus["ids"],corpus["metadatas"])}
    issues = validate_corpus(benchmark, {"chroma": inventory})
    if issues:
        raise ValueError("\n".join(issues))
    report = rescore(benchmark,saved)
    timestamp = datetime.now(timezone.utc)
    report["provenance"] = {"rescored_at_utc": timestamp.isoformat(), "source_results": str(SOURCE),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(), "benchmark": str(BENCHMARK),
        "benchmark_sha256": hashlib.sha256(BENCHMARK.read_bytes()).hexdigest(),
        "source_configuration": saved["configuration"], "retrieval_rerun": False,
        "chroma_collection": benchmark.corpus.collection_name, "corpus_validation_issues": issues,
        "validated_chroma_chunk_count": len(inventory), "rank_scope": "saved final top five"}
    output = Path("evaluation/results") / f"evidence_rescore_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}"
    output.with_suffix(".json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    output.with_suffix(".md").write_text(markdown(report),encoding="utf-8")
    print(json.dumps(report["aggregates"],indent=2))
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
