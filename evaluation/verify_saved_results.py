"""Reproduce published scores from saved results; no corpus/API/model access.

Evidence aggregates are recomputed from saved rankings, and the published
judge and RAGAS agreement with the human labels from saved judgments.
"""
import hashlib
import json
from pathlib import Path
from evaluation.benchmark import load_benchmark
from evaluation.judge_agreement import compare, dimension_agreement
from evaluation.ragas_data import calibrate
from evaluation.rescore_evidence import MODES, rescore
from evaluation.run_judge import calibration_cases, usable

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


RESULTS = Path("evaluation/results")
# Published in evaluation/JUDGE_CALIBRATION.md as (agreement, kappa to 2 decimals).
JUDGE_CALIBRATIONS = {
    "judge_v1": (RESULTS / "judge_calibration_v1_20261012T081253Z.json", {
        "completeness_points": ("141/144", 0.86), "correctness": ("58/64", 0.79), "groundedness": ("67/76", 0.69),
        "citation_correctness": ("51/64", 0.55), "refusal_correctness": ("12/13", 0.63)}),
    "judge_v2": (RESULTS / "judge_calibration_judge_v2_20261012T084333Z.json", {
        "completeness_points": ("140/144", 0.82), "correctness": ("57/64", 0.75), "groundedness": ("69/76", 0.75),
        "citation_correctness": ("53/64", 0.61), "refusal_correctness": ("12/13", 0.63)}),
}
# Published in evaluation/RAGAS_COMPARISON.md, on the 64 answers that are not exact refusals.
RAGAS_REPORT = RESULTS / "ragas_calibration_20261016T130348Z.json"
PUBLISHED_JUDGE_VS_RAGAS = {"groundedness": ("57/64", 0.73), "correctness": ("57/64", 0.75)}
# metric: (human label, best threshold, agreement, kappa)
PUBLISHED_RAGAS = {"faithfulness": ("groundedness", 0.9, "51/64", 0.58),
                   "factual_correctness": ("correctness", 0.8, "48/64", 0.48)}


def _published(agreement: dict) -> tuple:
    return agreement["agreement"], round(agreement["kappa"], 2)


def _check(name: str, recomputed: dict, published: dict):
    for dimension, expected in published.items():
        if recomputed[dimension] != expected:
            raise ValueError(f"{name} {dimension}: recomputed {recomputed[dimension]} != published {expected}")


def _check_human_labels(report: dict, rows: list[dict], key):
    """Saved rows must carry the human labels of the finalized reviews they cite."""
    for source in report["inputs"].values():
        if hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Historical input hash mismatch: {source['path']}")
    human = {f"{c['run']}/{c['question_id']}": c["human"] for c in calibration_cases()}
    for row in rows:
        if row["human"] != human[key(row)]:
            raise ValueError(f"Human labels differ from the reviews for {key(row)}")


def verify_judge_calibration(calibrations=JUDGE_CALIBRATIONS) -> dict:
    """Recompute the published judge and RAGAS agreement tables; raise on any difference."""
    table = {}
    for name, (path, published) in calibrations.items():
        report = json.loads(path.read_text(encoding="utf-8"))
        _check_human_labels(report, report["judgments"], lambda r: f"{r['run']}/{r['question_id']}")
        agreement = compare(usable(report["judgments"]))
        table[name] = {dimension: _published(agreement[dimension]) for dimension in published}
        _check(name, table[name], published)

    # Like for like with RAGAS: judge v2 on the answers that are not exact refusals.
    judged = usable(json.loads(calibrations["judge_v2"][0].read_text(encoding="utf-8"))["judgments"])
    answers = [c for c in judged if (c["answer"] or "").strip() != "I don't know."]
    table["judge_v2_vs_ragas"] = {
        dimension: _published(dimension_agreement(
            [(c["human"][dimension], c["judge"][dimension]) for c in answers if c["human"][dimension] in (0, 1)]))
        for dimension in PUBLISHED_JUDGE_VS_RAGAS}
    _check("judge_v2_vs_ragas", table["judge_v2_vs_ragas"], PUBLISHED_JUDGE_VS_RAGAS)

    ragas = json.loads(RAGAS_REPORT.read_text(encoding="utf-8"))
    _check_human_labels(ragas, ragas["rows"], lambda r: r["question_id"])
    table["ragas"] = {}
    for metric, (human_dimension, threshold, *expected) in PUBLISHED_RAGAS.items():
        thresholds = calibrate(ragas["rows"], metric, human_dimension)["thresholds"]
        best = max(thresholds, key=lambda t: t["kappa"])
        if best["threshold"] != threshold:
            raise ValueError(f"ragas {metric}: best threshold {best['threshold']} != published {threshold}")
        table["ragas"][metric] = _published(best)
    _check("ragas", table["ragas"], {metric: tuple(v[2:]) for metric, v in PUBLISHED_RAGAS.items()})
    return table


def main():
    for report in REPORTS:
        result = verify(report)
        print(f"Verified {report.name}: historical hashes, per-query scores and aggregates, without retrieval or generation.")
        for mode, values in result["aggregates"].items():
            metrics = values["evidence"]
            print(f"  {mode}: Evidence MRR={metrics['mrr']:.5f}; complete coverage@3={metrics['complete_at_3']:.5f}")
    table = verify_judge_calibration()
    print("Verified published judge and RAGAS agreement with the human labels, from saved judgments.")
    for name, rows in table.items():
        print(f"  {name}: " + "; ".join(f"{dimension} {agreement} (kappa {kappa:.2f})"
                                        for dimension, (agreement, kappa) in rows.items()))


if __name__ == "__main__":
    main()
