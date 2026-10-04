"""Validate benchmark schemas; optionally check references in persisted Chroma."""
import argparse
from pathlib import Path
from evaluation.benchmark import load_benchmark, validate_corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--corpus", action="store_true", help="Also check the existing .chroma collection")
    args = parser.parse_args()
    paths = args.paths or [Path("evaluation/benchmarks/retrieval_v1.json"),
                           Path("evaluation/benchmarks/retrieval_v2.json")]
    for path in paths:
        benchmark = load_benchmark(path)
        if args.corpus:
            import chromadb
            collection = chromadb.PersistentClient(path=".chroma").get_collection(benchmark.corpus.collection_name)
            records = collection.get(include=["metadatas"])
            inventory = {}
            for cid, meta in zip(records["ids"], records["metadatas"]):
                if not meta or meta.get("chunk_id") != cid or not meta.get("document_id") or cid in inventory:
                    raise ValueError("Invalid or duplicate Chroma chunk identity")
                inventory[cid] = meta["document_id"]
            issues = validate_corpus(benchmark, {"chroma": inventory})
            if issues:
                raise ValueError("\n".join(issues))
        answerable = sum(case.answerable for case in benchmark.cases)
        print(f"{path.as_posix()}: schema v{benchmark.schema_version}, {len(benchmark.cases)} cases, "
              f"{answerable} answerable; {'schema + Chroma' if args.corpus else 'schema'} valid")


if __name__ == "__main__":
    main()
