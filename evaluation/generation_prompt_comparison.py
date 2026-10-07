"""Official prompt comparison from finalized human reviews only; no judging."""
from copy import deepcopy
import argparse
import json
from pathlib import Path
from statistics import mean, median

from evaluation.generation_report import aggregate_review
from evaluation.generation_benchmark import file_hash
from evaluation.generation_human_review import REVIEWER_FIELDS

RESULTS = Path("evaluation/results")
SOURCES = {
    "generation_baseline_v1": "generation_baseline_v1",
    "grounded_strict_v1": "generation_strict_prompt_v1",
    "grounded_balanced_v2": "generation_balanced_prompt_v2",
}
JSON_PATH = RESULTS / "generation_prompt_ablation_comparison_v1.json"
MARKDOWN_PATH = JSON_PATH.with_suffix(".md")
FINAL_SOURCES = {**SOURCES, "grounded_strict_v2": "generation_strict_prompt_v2"}
FINAL_JSON_PATH = RESULTS / "generation_prompt_ablation_comparison_final.json"
FINAL_MARKDOWN_PATH = FINAL_JSON_PATH.with_suffix(".md")
TRANSITIONS = ("004", "007", "008", "010", "012", "013", "014", "017", "019")
LIMITATION = "Controlled 19-case benchmark (16 answerable, 3 refusal cases). Conclusions are limited to this evaluation set; no statistical significance is claimed."


def build_comparison(results=RESULTS, *, sources=None):
    results = Path(results)
    sources = SOURCES if sources is None else sources
    experiments, reviews = {}, {}
    for name, stem in sources.items():
        path = results / (stem + "_human_review.json")
        review = json.loads(path.read_text(encoding="utf-8"))
        # Mandatory gate: never reconstruct missing labels from aggregate totals.
        aggregate = aggregate_review(review)
        raw_path = results / (stem + ".json")
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        latency = [r["generation_latency_seconds"] for r in raw["queries"]]
        usages = [r["token_usage"] for r in raw["queries"] if r["token_usage"] is not None]
        answers = [r["generated_answer"] for r in raw["queries"]]
        experiments[name] = {
            **aggregate, "review": {"path": path.as_posix(), "sha256": file_hash(path)},
            "raw_run": {"path": raw_path.as_posix(), "sha256": file_hash(raw_path)},
            "generation_configuration": deepcopy(raw["configuration"]),
            "efficiency": {"case_count": len(answers), "latency_seconds": {
                "mean": mean(latency), "median": median(latency), "total": sum(latency)},
                "token_usage": {"available_case_count": len(usages), **{
                    key: sum(u[key] for u in usages) for key in ("prompt_tokens", "completion_tokens", "total_tokens")}},
                "average_answer_words": mean(len(a.split()) for a in answers),
                "average_answer_characters": mean(map(len, answers))},
        }
        unsupported_ids = [r["question_id"] for r in review["cases"] if r["unsupported_claims"]]
        experiments[name]["unsupported_elaboration"] = {
            "case_count": len(unsupported_ids), "eligible_count": len(review["cases"]),
            "value": len(unsupported_ids) / len(review["cases"]), "question_ids": unsupported_ids,
            "source": "Human-entered unsupported_claims only."}
        reviews[name] = review
    base = reviews["generation_baseline_v1"]
    for review in reviews.values():
        if review["rubric"] != base["rubric"] or review["instructions"] != base["instructions"]:
            raise ValueError("Review methodology differs")
        for old, new in zip(base["cases"], review["cases"]):
            for field in old.keys() - REVIEWER_FIELDS - {"generated_answer"}:
                if old[field] != new[field]:
                    raise ValueError("Frozen review content differs")
    transitions = []
    for suffix in TRANSITIONS:
        qid = "retrieval_" + suffix
        transitions.append({"question_id": qid, "experiments": {
            name: {key: deepcopy(row[key]) for key in (
                "correctness", "groundedness", "completeness_score", "refusal_correctness",
                "citation_correctness", "prompt_compliance", "unsupported_claims",
                "completeness_points", "evidence_group_coverage",
                "missing_required_points", "reviewer_notes")}
            for name, review in reviews.items() for row in review["cases"] if row["question_id"] == qid}})
    tradeoffs = [
        "Baseline: maximum completeness, poor groundedness/citation correctness, 14 unsupported-elaboration failures.",
        "Strict v1: strongest grounding and zero unsupported elaboration, but too conservative on some supported questions; one false refusal and under-answering.",
        "Balanced v2: recovers completeness and fixes the false refusal, but reintroduces unsupported content."]
    if "grounded_strict_v2" in sources:
        tradeoffs.append("Strict v2: targeted completeness refinement of Strict v1; fixes the false refusal and improves completeness, but still has one unsupported-elaboration case. Cases 008, 010, and 012 remain incomplete; case 013 contains unsupported elaboration. This demonstrates the measured completeness/grounding trade-off, not a universally best prompt.")
    return {"schema_version": 1, "finalized_validation": f"passed for all {len(sources)} reviews",
            "limitation": LIMITATION, "overall_score": "not computed",
            "measurement_policy": "Frozen generation measurements; words are whitespace splits including citations. Quality uses finalized human labels only; each dimension excludes its own N/A labels.",
            "experiments": experiments, "case_transitions": transitions,
            "tradeoffs": tradeoffs}


def render_comparison(report):
    names = list(report["experiments"])
    labels = {"generation_baseline_v1": "Baseline", "grounded_strict_v1": "Strict v1",
              "grounded_balanced_v2": "Balanced v2", "grounded_strict_v2": "Strict v2"}
    headers = " | ".join(labels[n] for n in names)
    separator = "| --- | " + " | ".join("---:" for _ in names) + " |"
    lines = ["# Controlled Grounded-Prompt Ablation", "", report["limitation"], "",
             "Finalized human labels only. Each dimension has its own eligible denominator; no weighted overall score.", "",
             f"| Dimension | {headers} |", separator]
    for key in ("correctness", "groundedness", "mean_completeness", "full_completeness_rate", "refusal_correctness", "citation_correctness", "prompt_compliance"):
        values = []
        for name in names:
            m = report["experiments"][name]["metrics"][key]
            numerator = m["score_sum"] if key == "mean_completeness" else m["passed_count"]
            values.append(f"{numerator:g}/{m['eligible_count']} ({m['value']:.2%})")
        lines.append("| " + key + " | " + " | ".join(values) + " |")
    lines.extend(["", f"| Failures / efficiency | {headers} |", separator])
    getters = {
        "Unsupported elaboration (cases / eligible)": lambda e: f"{e['unsupported_elaboration']['case_count']}/{e['unsupported_elaboration']['eligible_count']}",
        "Distinct cases failing a dimension": lambda e: e["failures"]["unique_failed_case_count"],
        **{f"Latency {k} (seconds)": (lambda e, k=k: round(e["efficiency"]["latency_seconds"][k], 3)) for k in ("mean", "median", "total")},
        **{k: (lambda e, k=k: e["efficiency"]["token_usage"][k]) for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
        **{k: (lambda e, k=k: round(e["efficiency"][k], 2)) for k in ("average_answer_words", "average_answer_characters")},
    }
    for label, getter in getters.items():
        lines.append("| " + label + " | " + " | ".join(str(getter(report["experiments"][n])) for n in names) + " |")
    lines.extend(["", *["- " + text for text in report["tradeoffs"]], "",
                  "Strict refusal correctness is 3/4 across all human-labeled refusal decisions, including the failed refusal on answerable case 004. Expected refusal cases alone pass 3/3. Strict prompt compliance similarly includes case 004 (3/4).", "",
                  "## Reviewed case transitions", "", "Cells show correctness / groundedness / completeness / citation correctness / refusal correctness / prompt compliance, followed by failed point IDs and supplied issues or notes. N/A remains excluded. Exact point judgments and evidence-group coverage are recorded in the JSON.", "",
                  f"| Case | {headers} |", "| --- | " + " | ".join("---" for _ in names) + " |"])
    for transition in report["case_transitions"]:
        cells = []
        for name in names:
            row = transition["experiments"][name]
            scores = " / ".join(str(row[k]) for k in ("correctness", "groundedness", "completeness_score", "citation_correctness", "refusal_correctness", "prompt_compliance"))
            missing = ["Failed points: " + ", ".join(row["missing_required_points"])] if row["missing_required_points"] else []
            issues = "; ".join([*missing, *row["unsupported_claims"], row["reviewer_notes"]]).strip("; ")
            cells.append((scores + (" — " + issues if issues else "")).replace("|", "\\|"))
        lines.append("| " + transition["question_id"] + " | " + " | ".join(cells) + " |")
    filename = FINAL_JSON_PATH.name if "grounded_strict_v2" in names else JSON_PATH.name
    lines.extend(["", f"[Comparison JSON]({filename})", ""])
    return "\n".join(lines)


def write_comparison(json_path=JSON_PATH, markdown_path=MARKDOWN_PATH, *, final=False):
    json_path, markdown_path = Path(json_path), Path(markdown_path)
    if json_path.resolve() == markdown_path.resolve() or json_path.exists() or markdown_path.exists():
        raise FileExistsError("Comparison outputs must be distinct new files")
    report = build_comparison(sources=FINAL_SOURCES) if final else build_comparison()
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_comparison(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", action="store_true", help="Compare all four finalized reviews")
    args = parser.parse_args()
    write_comparison(FINAL_JSON_PATH, FINAL_MARKDOWN_PATH, final=True) if args.final else write_comparison()
