"""Run from the repository root: python -m evaluation.run_retrieval_benchmark."""

from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean
import time

from evaluation.benchmark import Benchmark, load_benchmark, validate_corpus
from evaluation.metrics import hit_at_k, recall_at_k, reciprocal_rank

MODES = ("vector", "bm25", "hybrid", "hybrid_reranked")
K = 5
CANDIDATE_K = 10
BENCHMARK_PATH = Path("evaluation/benchmarks/retrieval_v1.json")
METRIC_NAMES = (
    "hit_at_1", "hit_at_3", "hit_at_5",
    "recall_at_1", "recall_at_3", "recall_at_5", "reciprocal_rank",
)


def score_query(retrieved_ids: list[str], relevant_ids: list[str]) -> dict:
    scores = {}
    for cutoff in (1, 3, 5):
        scores[f"hit_at_{cutoff}"] = hit_at_k(retrieved_ids, relevant_ids, cutoff)
        scores[f"recall_at_{cutoff}"] = recall_at_k(retrieved_ids, relevant_ids, cutoff)
    scores["reciprocal_rank"] = reciprocal_rank(retrieved_ids, relevant_ids)
    return scores


def aggregate_results(queries: list[dict]) -> dict:
    """Macro-average quality over answerable cases; latency over all cases.

    Empty denominators produce None. MRR is bounded by the five returned chunks.
    """
    aggregates = {}
    answerable = [query for query in queries if query["answerable"]]
    for mode in MODES:
        scores = {}
        for metric in METRIC_NAMES:
            values = [query["results"][mode]["metrics"][metric] for query in answerable]
            values = [value for value in values if value is not None]
            name = "mrr" if metric == "reciprocal_rank" else metric
            scores[name] = mean(values) if values else None
        latencies = [query["results"][mode]["latency_seconds"] for query in queries]
        aggregates[mode] = {
            "quality_query_count": len(answerable),
            "latency_query_count": len(queries),
            "metrics": scores,
            "mean_latency_seconds": mean(latencies) if latencies else None,
        }
    return aggregates


def run_cases(benchmark: Benchmark, store, retrieve_fn=None) -> list[dict]:
    """Use the existing retrieval abstraction, with fixed per-backend depths."""
    if retrieve_fn is None:
        from evaluation.retrieval import retrieve
        retrieve_fn = retrieve
    queries = []
    for case in benchmark.cases:
        relevant_ids = [chunk.chunk_id for chunk in case.relevant_chunks]
        results = {}
        for mode in MODES:
            started = time.perf_counter()
            chunks = retrieve_fn(
                store, case.question, mode=mode, k=K, candidate_k=CANDIDATE_K,
            )
            latency = time.perf_counter() - started
            returned_ids = []
            for chunk in chunks:
                if not chunk.chunk_id:
                    raise ValueError(f"{case.question_id}/{mode}: result missing persisted chunk_id")
                returned_ids.append(chunk.chunk_id)
            results[mode] = {
                "retrieved_chunk_ids": returned_ids,
                "latency_seconds": latency,
                "metrics": score_query(returned_ids, relevant_ids),
            }
        queries.append({
            "question_id": case.question_id,
            "question": case.question,
            "category": case.category,
            "answerable": case.answerable,
            "relevant_document_ids": case.relevant_document_ids,
            "relevant_chunk_ids": relevant_ids,
            "notes": case.notes,
            "results": results,
        })
        print(f"Completed {case.question_id}", flush=True)
    return queries


def corpus_inventories(store) -> dict:
    """Read existing records; never create a Whoosh index or use the catalog."""
    from whoosh import index
    from app.vectordb.whoosh_index import INDEX_DIR

    records = store.collection.get(include=["metadatas"])
    chroma_inventory = {}
    for record_id, metadata in zip(records["ids"], records["metadatas"]):
        metadata = metadata or {}
        chunk_id = metadata.get("chunk_id")
        document_id = metadata.get("document_id")
        if not chunk_id or not document_id or chunk_id != record_id:
            raise ValueError(f"Invalid Chroma identity or document metadata: {record_id}")
        if chunk_id in chroma_inventory:
            raise ValueError(f"Duplicate Chroma chunk ID: {chunk_id}")
        chroma_inventory[chunk_id] = document_id

    whoosh_inventory = {}
    ix = index.open_dir(str(INDEX_DIR))
    try:
        with ix.reader() as reader:
            for metadata in reader.all_stored_fields():
                chunk_id = metadata.get("chunk_id")
                document_id = metadata.get("document_id")
                if not chunk_id or not document_id:
                    raise ValueError("Whoosh record missing chunk or document ID")
                if chunk_id in whoosh_inventory:
                    raise ValueError(f"Duplicate Whoosh chunk ID: {chunk_id}")
                whoosh_inventory[chunk_id] = document_id
    finally:
        ix.close()
    return {"chroma": chroma_inventory, "whoosh": whoosh_inventory}


def print_summary(aggregates: dict) -> None:
    print("\nMode              H@1   H@3   H@5   R@1   R@3   R@5   MRR   Mean ms")
    for mode, aggregate in aggregates.items():
        values = aggregate["metrics"].values()
        scores = " ".join(f"{value:5.3f}" if value is not None else "  n/a" for value in values)
        latency = aggregate["mean_latency_seconds"]
        latency_text = f"{latency * 1000:.1f}" if latency is not None else "n/a"
        print(f"{mode:17} {scores} {latency_text:>9}")


def main() -> Path:
    benchmark = load_benchmark(BENCHMARK_PATH)
    import chromadb
    from app.vectordb.chroma_store import ChromaStore

    client = chromadb.PersistentClient(path=".chroma")
    collection = client.get_collection(benchmark.corpus.collection_name)
    # Reuse the production adapter without its get-or-create constructor.
    store = ChromaStore.__new__(ChromaStore)
    store.client = client
    store.collection = collection
    inventories = corpus_inventories(store)
    for name, inventory in inventories.items():
        issues = validate_corpus(benchmark, {name: inventory})
        if issues:
            raise ValueError("Gold corpus validation failed:\n" + "\n".join(issues))
    corpus_issues = validate_corpus(benchmark, inventories)
    for issue in corpus_issues:
        print(issue, flush=True)

    started_at = datetime.now(timezone.utc)
    queries = run_cases(benchmark, store)
    aggregates = aggregate_results(queries)
    report = {
        "result_schema_version": 1,
        "benchmark_path": BENCHMARK_PATH.as_posix(),
        "benchmark_schema_version": benchmark.schema_version,
        "started_at_utc": started_at.isoformat(),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": {"modes": list(MODES), "candidate_k": CANDIDATE_K, "k": K},
        "corpus": {
            "collection_name": benchmark.corpus.collection_name,
            "chroma_path": ".chroma",
            "whoosh_path": "data/whoosh_index",
            "chunk_counts": {name: len(inventory) for name, inventory in inventories.items()},
            "validation_issues": corpus_issues,
        },
        "aggregation": {
            "quality": "macro mean over answerable cases only; undefined values excluded",
            "mrr": "mean reciprocal rank within the final five returned results",
            "latency": "mean over all queries; seconds; includes embedding requests",
            "execution_order": "benchmark order; modes sequential in configuration order; no warmup",
        },
        "queries": queries,
        "aggregates": aggregates,
    }
    output = Path("evaluation/results") / f"{BENCHMARK_PATH.stem}_{started_at.strftime('%Y%m%dT%H%M%S%fZ')}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print_summary(aggregates)
    print(f"\nRaw results: {output}")
    return output


if __name__ == "__main__":
    main()
