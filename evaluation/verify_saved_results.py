"""Reproduce final evidence aggregates from saved rankings; no corpus/API/model access."""
import hashlib
import json
from pathlib import Path
from evaluation.benchmark import load_benchmark
from evaluation.rescore_evidence import MODES, rescore

REPORT = Path("evaluation/results/evidence_rescore_20261004T100113793072Z.json")
REPORTS = (REPORT, Path("evaluation/results/evidence_rescore_20261013T141146718706Z.json"))


def verify(report_path=REPORT):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    provenance = report["provenance"]
    # Historical Windows-relative paths must also work on Linux/macOS clones.
    source_path = Path(provenance["source_results"].replace("\\", "/"))
    benchmark_path = Path(provenance["benchmark"].replace("\\", "/"))
    for path, expected in ((source_path, provenance["source_sha256"]),
                           (benchmark_path, provenance["benchmark_sha256"])):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Historical input hash mismatch: {path.as_posix()}")
    # Reports written before modes were recorded used the default hybrid orderings.
    modes = tuple(provenance.get("modes", MODES))
    result = rescore(load_benchmark(benchmark_path), json.loads(source_path.read_text(encoding="utf-8")), modes)
    if result["aggregates"] != report["aggregates"]:
        raise ValueError("Recomputed evidence aggregates differ from the saved report")
    if result["queries"] != report["queries"]:
        raise ValueError("Recomputed per-query scores differ from the saved report")
    return result


def main():
    for report in REPORTS:
        result = verify(report)
        print(f"Verified {report.name}: historical hashes, per-query scores and aggregates, without retrieval or generation.")
        for mode, values in result["aggregates"].items():
            metrics = values["evidence"]
            print(f"  {mode}: Evidence MRR={metrics['mrr']:.5f}; complete coverage@3={metrics['complete_at_3']:.5f}")


if __name__ == "__main__":
    main()
