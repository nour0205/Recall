"""Evaluation-only paired comparison: one RRF pool per query, unchanged reranker.

Run from repository root: python -m evaluation.run_reranker_ablation
"""

from datetime import datetime, timezone
import json
from pathlib import Path

from evaluation.benchmark import load_benchmark, validate_corpus
from evaluation.run_retrieval_benchmark import BENCHMARK_PATH, CANDIDATE_K, K, score_query


def hybrid_pool(store, question):
    from app.rag.hybrid_retriever import (
        retrieve_vector_candidates, retrieve_bm25_candidates, reciprocal_rank_fusion,
    )
    return reciprocal_rank_fusion(
        retrieve_vector_candidates(store, question, k=CANDIDATE_K),
        retrieve_bm25_candidates(question, k=CANDIDATE_K),
    )


def rank_change(before, after):
    """Missing from the candidate pool ranks below any retrieved position."""
    if before == after:
        return "unchanged"
    if before is None:
        return "improved"
    if after is None:
        return "worsened"
    return "improved" if after < before else "worsened"


def compare_case(case, pool, rerank_fn=None):
    from app.rag.reranker import rerank_items, keyword_overlap_score, tokenize, STOPWORDS
    if rerank_fn is None:
        rerank_fn = rerank_items
    # Sort the full shared pool once; output selection happens after reranking.
    ranked = rerank_fn(case.question, pool, k=len(pool))
    before = {item.chunk_id: rank for rank, item in enumerate(pool, 1)}
    after = {item.chunk_id: rank for rank, item in enumerate(ranked, 1)}
    gold = [chunk.chunk_id for chunk in case.relevant_chunks]
    canonical_ranks = [{
        "chunk_id": cid, "before": before.get(cid), "after": after.get(cid),
        "change": rank_change(before.get(cid), after.get(cid)),
    } for cid in gold]
    earliest_before = min((before[cid] for cid in gold if cid in before), default=None)
    earliest_after = min((after[cid] for cid in gold if cid in after), default=None)
    visible_before = earliest_before if earliest_before is not None and earliest_before <= K else None
    visible_after = earliest_after if earliest_after is not None and earliest_after <= K else None
    query_tokens = [token for token in tokenize(case.question) if token not in STOPWORDS]
    details = []
    for item in ranked:
        matched = [token for token in query_tokens if token in set(tokenize(item.text.strip()))]
        lexical = keyword_overlap_score(case.question, item.text.strip())
        details.append({
            "chunk_id": item.chunk_id, "document_id": item.document_id,
            "text": item.text, "before_rank": before[item.chunk_id],
            "after_rank": after[item.chunk_id], "matched_tokens": matched,
            "overlap_count": len(matched), "phrase_bonus": lexical - len(matched),
            "rank_bonus": item.rerank_score - lexical,
            "rerank_score": item.rerank_score, "hybrid_score": item.hybrid_score,
        })
    before_ids = [item.chunk_id for item in pool[:K]]
    after_ids = [item.chunk_id for item in ranked[:K]]
    return {
        "question_id": case.question_id, "question": case.question,
        "answerable": case.answerable, "notes": case.notes,
        "relevant_chunk_ids": gold, "canonical_ranks": canonical_ranks,
        "earliest_canonical_rank_before": earliest_before,
        "earliest_canonical_rank_after": earliest_after,
        "rank_change": rank_change(earliest_before, earliest_after) if case.answerable else None,
        "final_k_rank_change": rank_change(visible_before, visible_after) if case.answerable else None,
        "pool_ids": [item.chunk_id for item in pool],
        "reranked_pool_ids": [item.chunk_id for item in ranked],
        "hybrid": {"retrieved_chunk_ids": before_ids, "metrics": score_query(before_ids, gold)},
        "hybrid_reranked": {"retrieved_chunk_ids": after_ids, "metrics": score_query(after_ids, gold)},
        "top_3_changed": before_ids[:3] != after_ids[:3],
        "heuristic_contributions": details,
    }


def run_ablation(benchmark, store, pool_fn=None):
    provider = hybrid_pool if pool_fn is None else pool_fn
    queries = []
    for case in benchmark.cases:
        queries.append(compare_case(case, provider(store, case.question)))
        print(f"Completed {case.question_id}", flush=True)
    return queries


def aggregate(queries):
    from statistics import mean
    answerable = [query for query in queries if query["answerable"]]
    result = {"answerable_count": len(answerable)}
    for field in ("rank_change", "final_k_rank_change"):
        result[field] = {change: sum(q[field] == change for q in answerable)
                         for change in ("improved", "unchanged", "worsened")}
    for mode in ("hybrid", "hybrid_reranked"):
        result[mode] = {}
        for key in ("hit_at_1", "hit_at_3", "hit_at_5", "recall_at_1", "recall_at_3", "recall_at_5", "reciprocal_rank"):
            values = [q[mode]["metrics"][key] for q in answerable]
            result[mode]["mrr" if key == "reciprocal_rank" else key] = mean(values) if values else None
    return result


def main():
    import chromadb
    from app.vectordb.chroma_store import ChromaStore
    from evaluation.run_retrieval_benchmark import corpus_inventories
    benchmark = load_benchmark(BENCHMARK_PATH)
    client = chromadb.PersistentClient(path=".chroma")
    store = ChromaStore.__new__(ChromaStore)
    store.client = client
    store.collection = client.get_collection(benchmark.corpus.collection_name)
    inventories = corpus_inventories(store)
    for name, inventory in inventories.items():
        issues = validate_corpus(benchmark, {name: inventory})
        if issues:
            raise ValueError("\n".join(issues))
    timestamp = datetime.now(timezone.utc)
    queries = run_ablation(benchmark, store)
    report = {
        "started_at_utc": timestamp.isoformat(),
        "benchmark_path": str(BENCHMARK_PATH),
        "configuration": {"candidate_k": CANDIDATE_K, "k": K, "one_shared_pool_per_query": True},
        "rank_semantics": "Earliest canonical rank in full pool; per-chunk ranks also reported. Final-k counts treat ranks beyond five as absent. Equivalent evidence does not alter scores; promotions require manual review.",
        "corpus_validation_issues": validate_corpus(benchmark, inventories),
        "queries": queries, "aggregates": aggregate(queries),
    }
    output = Path("evaluation/results") / f"reranker_ablation_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(report["aggregates"], indent=2))
    print(f"Raw ablation: {output}")


if __name__ == "__main__":
    main()
