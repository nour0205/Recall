"""Check that the vector and keyword indexes hold the same chunks.

Usage, from the repository root:
    python -m app.check_indexes            # report only
    python -m app.check_indexes --repair   # make the keyword index match the vector index

Repair makes no API calls: keyword entries missing from Whoosh are rebuilt from
the text stored in Chroma, and Whoosh entries with no Chroma chunk are removed.
"""
import argparse
import json

import chromadb

from app.library import check_consistency, repair
from app.vectordb.chroma_store import ChromaStore

COLLECTION = "api-demo"


def open_store(persist_dir: str = ".chroma") -> ChromaStore:
    store = ChromaStore.__new__(ChromaStore)
    store.client = chromadb.PersistentClient(path=persist_dir)
    store.collection = store.client.get_or_create_collection(COLLECTION)
    return store


def main(apply_repair: bool = False) -> dict:
    store = open_store()
    report = check_consistency(store)
    print(json.dumps(report, indent=2))
    if not report["consistent"] and apply_repair:
        print(json.dumps(repair(store), indent=2))
        report = check_consistency(store)
        print("Consistent after repair:", report["consistent"])
    elif not report["consistent"]:
        print("Indexes differ. Run with --repair to make the keyword index match the vector index.")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repair", action="store_true")
    main(parser.parse_args().repair)
