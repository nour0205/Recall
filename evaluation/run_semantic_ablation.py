"""Three orderings of one full RRF pool. Run from repository root."""
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

from evaluation.benchmark import load_benchmark, validate_corpus
from evaluation.run_retrieval_benchmark import BENCHMARK_PATH, CANDIDATE_K, K, score_query, corpus_inventories
from evaluation.run_reranker_ablation import hybrid_pool, compare_case, aggregate, rank_change
from evaluation.semantic_reranker import SemanticReranker


def compare_semantic(case, pool, reranker):
    row = compare_case(case, pool)
    flags = reranker.truncation_flags(case.question, pool) if pool else []
    start = perf_counter()
    ranked = reranker.rerank(case.question, pool, k=len(pool)) if pool else []
    elapsed = perf_counter() - start
    before = {c.chunk_id: i for i, c in enumerate(pool, 1)}
    after = {c.chunk_id: i for i, c in enumerate(ranked, 1)}
    gold = row["relevant_chunk_ids"]
    earliest = min((after[c] for c in gold if c in after), default=None)
    ids = [c.chunk_id for c in ranked[:K]]
    row["hybrid_semantic_reranked"] = {
        "retrieved_chunk_ids": ids, "metrics": score_query(ids, gold),
        "inference_latency_seconds": elapsed,
        "earliest_canonical_rank": earliest,
        "rank_change": rank_change(row["earliest_canonical_rank_before"], earliest) if case.answerable else None,
        "canonical_ranks": [{"chunk_id": c, "before": before.get(c), "after": after.get(c),
                             "change": rank_change(before.get(c), after.get(c))} for c in gold],
        "truncated_chunk_ids": [c.chunk_id for c, flag in zip(pool, flags) if flag],
        "ranked_pool": [dict(c.model_dump(), original_rrf_rank=before[c.chunk_id], semantic_rank=i)
                        for i, c in enumerate(ranked, 1)],
        "promoted_noncanonical_candidates": [c.chunk_id for c in ranked[:K]
            if c.chunk_id not in gold and after[c.chunk_id] < before[c.chunk_id]],
        "manual_review": None,
    }
    return row


def summarize(queries):
    result = aggregate(queries)
    answerable = [q for q in queries if q["answerable"]]
    mode = "hybrid_semantic_reranked"
    result[mode] = {("mrr" if key == "reciprocal_rank" else key): mean(q[mode]["metrics"][key] for q in answerable)
                   for key in ("hit_at_1", "hit_at_3", "hit_at_5", "recall_at_1", "recall_at_3", "recall_at_5", "reciprocal_rank")}
    result["semantic_rank_change"] = {s: sum(q[mode]["rank_change"] == s for q in answerable)
                                       for s in ("improved", "unchanged", "worsened")}
    result["semantic_latency_seconds"] = {"mean": mean(q[mode]["inference_latency_seconds"] for q in queries),
        "per_query": {q["question_id"]: q[mode]["inference_latency_seconds"] for q in queries}}
    return result


def markdown(report):
    lines = ["# Shared-pool MiniLM ablation", "", "Canonical labels only; alternatives never count automatically.",
             "One full union per query: top 10 per backend, final top 5. Full-pool earliest canonical rank determines change counts.",
             "", "## Configuration", "", "```json", json.dumps(report["configuration"], indent=2), "```",
             "", "## Aggregates", "", "```json", json.dumps(report["aggregates"], indent=2), "```"]
    for q in report["queries"]:
        s = q["hybrid_semantic_reranked"]
        lines += ["", f"## {q['question_id']}: {q['question']}", "", f"Answerable: {q['answerable']}. Notes: {q['notes']}",
                  f"Canonical ranks: {json.dumps(s['canonical_ranks'])}",
                  f"Semantic latency: {s['inference_latency_seconds']:.6f}s. Truncated pairs: {s['truncated_chunk_ids']}",
                  f"Manual promotion review: {json.dumps(s['manual_review'])}"]
        for mode in ("hybrid", "hybrid_reranked", "hybrid_semantic_reranked"):
            lines += ["", f"**{mode}**", "", f"Metrics: {json.dumps(q[mode]['metrics'])}",
                      f"Ranked top five UUIDs: {json.dumps(q[mode]['retrieved_chunk_ids'])}"]
        lines += ["", "| Semantic rank | RRF rank | Document | Chunk UUID | Semantic score |", "|---|---|---|---|---|"]
        for c in s["ranked_pool"]:
            lines.append(f"| {c['semantic_rank']} | {c['original_rrf_rank']} | {c['document_id']} | {c['chunk_id']} | {c['semantic_score']:.8f} |")
    return "\n".join(lines) + "\n"


def main():
    import chromadb
    from app.vectordb.chroma_store import ChromaStore
    benchmark = load_benchmark(BENCHMARK_PATH)
    store = ChromaStore.__new__(ChromaStore)
    store.client = chromadb.PersistentClient(path=".chroma")
    store.collection = store.client.get_collection(benchmark.corpus.collection_name)
    inventories = corpus_inventories(store)
    for name, inventory in inventories.items():
        issues = validate_corpus(benchmark, {name: inventory})
        if issues:
            raise ValueError("\n".join(issues))
    timestamp = datetime.now(timezone.utc)
    start = perf_counter()
    reranker = SemanticReranker()
    load_seconds = perf_counter() - start
    # Warm up separately; do not include download, loading, or warmup in query latency.
    start = perf_counter()
    reranker.scorer.predict([("warmup", "A short warmup passage.")], show_progress_bar=False)
    warmup_seconds = perf_counter() - start
    queries = []
    for case in benchmark.cases:
        queries.append(compare_semantic(case, hybrid_pool(store, case.question), reranker))
        print(f"Completed {case.question_id}", flush=True)
    report = {"started_at_utc": timestamp.isoformat(), "benchmark_path": str(BENCHMARK_PATH),
        "configuration": dict(reranker.configuration(), candidate_k=CANDIDATE_K, k=K,
            one_shared_pool_per_query=True, loading_download_seconds=load_seconds, warmup_seconds=warmup_seconds),
        "corpus_validation_issues": validate_corpus(benchmark, inventories),
        "queries": queries, "aggregates": summarize(queries)}
    output = Path("evaluation/results") / f"semantic_ablation_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix(".json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregates"], indent=2))
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
