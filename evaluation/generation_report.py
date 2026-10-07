"""Deterministic aggregates of finalized human labels; never judge answers.

N/A labels are excluded separately for each dimension. Completeness is the
unweighted case mean over answerable cases. No combined score is produced.
"""

import argparse
from copy import deepcopy
import json
from pathlib import Path
from statistics import mean

from evaluation.generation_benchmark import canonical_hash, file_hash
from evaluation.generation_human_review import (
    BASELINE_PATH, LABEL_FIELDS, REVIEW_PATH, validate_workspace,
)

SUMMARY_PATH = Path("evaluation/results/generation_baseline_v1_summary.json")
MARKDOWN_PATH = Path("evaluation/results/generation_baseline_v1_summary.md")


def binary_metric(rows, field):
    eligible = [row for row in rows if type(row[field]) is int]
    passed = [row["question_id"] for row in eligible if row[field] == 1]
    failed = [row["question_id"] for row in eligible if row[field] == 0]
    return {
        "value": len(passed) / len(eligible) if eligible else None,
        "passed_count": len(passed), "failed_count": len(failed),
        "eligible_count": len(eligible), "excluded_na_count": len(rows) - len(eligible),
        "eligible_question_ids": [row["question_id"] for row in eligible],
        "failed_question_ids": failed,
    }


def aggregate_review(workspace):
    """Read validated human decisions only; return aggregates without mutation."""
    if workspace.get("review_status") != "finalized":
        raise ValueError("Aggregation requires review_status=finalized")
    errors = validate_workspace(workspace, finalized=True)
    if errors:
        raise ValueError("Finalized human-label validation failed:\n" + "\n".join(errors))
    rows = workspace["cases"]
    metrics = {field: binary_metric(rows, field) for field in LABEL_FIELDS}
    complete = [row for row in rows if row["expected_behavior"] == "answer"]
    scores = [row["completeness_score"] for row in complete]
    metrics["mean_completeness"] = {
        "value": mean(scores) if scores else None,
        "score_sum": sum(scores), "eligible_count": len(complete),
        "excluded_na_count": len(rows) - len(complete),
        "eligible_question_ids": [row["question_id"] for row in complete],
    }
    full = [row for row in complete if row["completeness_score"] == 1]
    incomplete = [row["question_id"] for row in complete if row["completeness_score"] < 1]
    metrics["full_completeness_rate"] = {
        "value": len(full) / len(complete) if complete else None,
        "passed_count": len(full), "failed_count": len(incomplete),
        "eligible_count": len(complete), "excluded_na_count": len(rows) - len(complete),
        "eligible_question_ids": [row["question_id"] for row in complete],
        "failed_question_ids": incomplete,
    }
    failed_ids = {qid for field in (*LABEL_FIELDS, "full_completeness_rate")
                  for qid in metrics[field]["failed_question_ids"]}
    # Categories summarize reviewer-provided issues/labels, never answer text.
    categories = [
        ("unsupported elaboration / over-generation", [row["question_id"] for row in rows if row["unsupported_claims"]],
         "Human-entered unsupported_claims; no automatic claim inspection."),
        ("refusal output-format noncompliance", [row["question_id"] for row in rows
                                                if row["expected_behavior"] == "refuse" and row["prompt_compliance"] == 0],
         "Human prompt_compliance=0 on a refusal case; see reviewer_notes for the stated reason."),
        ("answer prompt noncompliance", [row["question_id"] for row in rows
                                         if row["expected_behavior"] == "answer" and row["prompt_compliance"] == 0],
         "Human prompt_compliance=0 on an answerable case."),
        ("missing required points", [row["question_id"] for row in rows if row["missing_required_points"]],
         "Human-entered missing_required_points."),
        ("citation issues", [row["question_id"] for row in rows if row["citation_issues"]],
         "Human-entered citation_issues; distinct from the citation-correctness failure count."),
    ]
    return {
        "metrics": metrics,
        "failures": {
            "dimension_failed_counts": {**{field: metrics[field]["failed_count"] for field in LABEL_FIELDS},
                                        "incomplete_answers": len(incomplete)},
            "unique_failed_case_count": len(failed_ids),
            "failed_question_ids": [row["question_id"] for row in rows if row["question_id"] in failed_ids],
            "categories": [{"category": name, "case_count": len(ids), "question_ids": ids, "source": source}
                           for name, ids, source in categories if ids],
            "category_count_policy": "Case counts within each category; categories can overlap and are not summed into a quality score.",
            "reviewer_issue_details": [
                {"question_id": row["question_id"], **{field: deepcopy(row[field]) for field in
                  ("unsupported_claims", "missing_required_points", "citation_issues", "reviewer_notes")}}
                for row in rows if row["unsupported_claims"] or row["missing_required_points"]
                or row["citation_issues"] or row["reviewer_notes"]
            ],
        },
    }


def build_summary(review_path=REVIEW_PATH):
    review_path = Path(review_path)
    workspace = json.loads(review_path.read_text(encoding="utf-8"))
    aggregate = aggregate_review(workspace)  # Validate before computing any metrics.
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    operation = baseline["operational_summary"]
    rows = workspace["cases"]
    return {
        "summary_schema_version": 1,
        "human_review_status": "finalized", "finalized_validation": "passed",
        "scoring_source": "Supplied human-review labels only; no automated answer judging or inferred labels.",
        "human_review_artifact": {"path": review_path.as_posix(), "sha256": file_hash(review_path),
                                  "canonical_content_sha256": canonical_hash(workspace)},
        "frozen_source_artifacts": deepcopy(workspace["source_artifacts"]),
        "aggregation_policy": {
            "binary_dimensions": "Pass count / eligible count, excluding N/A separately for each dimension.",
            "mean_completeness": "Unweighted mean of human completeness_score across answerable cases only.",
            "full_completeness_rate": "Answerable cases with completeness_score=1 / all answerable cases.",
            "zero_eligible_cases": "Metric value is null; denominator and counts remain zero.",
            "overall_score": "Not computed; dimensions remain separate.",
        },
        "case_counts": {"total": len(rows), "answerable": sum(row["expected_behavior"] == "answer" for row in rows),
                        "refusal": sum(row["expected_behavior"] == "refuse" for row in rows),
                        "answerable_with_sufficient_context": sum(row["expected_behavior"] == "answer"
                                                                 and row["retrieved_context_sufficient"] is True for row in rows),
                        "completed_generations": operation["completed_generations"]},
        **aggregate,
        "generation_configuration": deepcopy(baseline["configuration"]),
        "generation_latency_seconds": deepcopy(operation["generation_latency_seconds"]),
        "token_usage": deepcopy(operation["token_usage"]),
        "api_runtime_failures": deepcopy(operation["failures"]),
        "corpus_validation_issues": deepcopy(baseline["corpus"]["validation_issues"]),
        "measurement_policy": "Generation latency and token usage copied from the frozen baseline; no generation rerun. Token usage covers generation, not embedding calls.",
    }


def render_summary(summary):
    metrics = summary["metrics"]
    counts = summary["case_counts"]
    lines = ["# Generation Baseline v1 — Human-Reviewed Results", "",
             f"{counts['total']} completed generations: {counts['answerable']} answerable cases and {counts['refusal']} refusal cases. "
             f"All {counts['answerable_with_sufficient_context']} answerable cases had sufficient retrieved evidence.", "",
             "Finalized validation passed. Results use the supplied human labels exactly; no LLM judge, RAGAS, or weighted overall score.", "",
             "[Finalized labels](generation_baseline_v1_human_review.json) · [Summary JSON](generation_baseline_v1_summary.json) · [Frozen raw baseline](generation_baseline_v1.json)", "",
             "| Dimension | Result | Eligible cases | N/A excluded |", "| --- | ---: | ---: | ---: |"]
    names = (("correctness", "Correctness"), ("groundedness", "Groundedness"),
             ("mean_completeness", "Mean completeness"), ("full_completeness_rate", "Full-completeness rate"),
             ("refusal_correctness", "Refusal correctness"), ("citation_correctness", "Citation correctness"),
             ("prompt_compliance", "Prompt compliance"))
    for key, name in names:
        metric = metrics[key]
        if metric["value"] is None:
            result = "N/A"
        elif key == "mean_completeness":
            result = f"{metric['value']:.3f}"
        else:
            result = f"{metric['passed_count']}/{metric['eligible_count']} ({metric['value']:.2%})"
        lines.append(f"| {name} | {result} | {metric['eligible_count']} | {metric['excluded_na_count']} |")
    lines.extend(["", "Each dimension excludes its own N/A labels. Binary metrics include cases with an integer label. Completeness covers answerable cases only; eligible IDs are recorded in the summary JSON.", "",
                  "Required-point completeness is reported separately. Full completeness does not override a human-labeled unsupported claim.", "",
                  "## Human-reported failures", "", "| Dimension | Failed cases |", "| --- | ---: |"])
    names_by_key = dict(names)
    for field, count in summary["failures"]["dimension_failed_counts"].items():
        lines.append(f"| {names_by_key.get(field, 'Incomplete answers')} | {count} |")
    lines.extend(["", f"Distinct cases failing at least one evaluated dimension: **{summary['failures']['unique_failed_case_count']}**. Counts across dimensions overlap.", "",
                  "| Qualitative category | Cases |", "| --- | ---: |"])
    lines.extend(f"| {category['category']} | {category['case_count']} |" for category in summary["failures"]["categories"])
    lines.extend(["", "Categories summarize reviewer-entered issues and labels. They do not come from a new inspection of generated answers.", "",
                  "| Case | Supplied reviewer issue / note |", "| --- | --- |"])
    for detail in summary["failures"]["reviewer_issue_details"]:
        text = "; ".join([*detail["unsupported_claims"], *detail["citation_issues"], detail["reviewer_notes"]]).strip("; ")
        lines.append(f"| {detail['question_id']} | {text.replace('|', chr(92) + '|')} |")
    latency = summary["generation_latency_seconds"]
    usage = summary["token_usage"]
    lines.extend(["", "## Recorded execution", "",
                  "Vector + BM25 + RRF, top 5 chunks; GPT-4o-mini, temperature 0, max_tokens 800. The production prompt was unchanged.", "",
                  f"Generation latency over {latency['count']} cases: mean **{latency['mean']:.3f}s**, median **{latency['median']:.3f}s**, "
                  f"range **{latency['min']:.3f}–{latency['max']:.3f}s**, total **{latency['total']:.3f}s**.", "",
                  f"Generation tokens across {usage['available_case_count']} cases: **{usage['prompt_tokens']:,} input + {usage['completion_tokens']:,} output = {usage['total_tokens']:,} total**. Embedding tokens are excluded.", "",
                  f"API/runtime failures: **{len(summary['api_runtime_failures'])}**. Latency and usage were copied from the frozen baseline; generation was not rerun.", ""])
    if summary["corpus_validation_issues"]:
        lines.extend(["Existing corpus inventory issue retained from the baseline:", ""])
        lines.extend(f"- {issue}" for issue in summary["corpus_validation_issues"])
        lines.append("")
    return "\n".join(lines)


def write_report(review_path=REVIEW_PATH, summary_path=SUMMARY_PATH, markdown_path=MARKDOWN_PATH):
    summary_path, markdown_path = Path(summary_path), Path(markdown_path)
    if summary_path.resolve() == markdown_path.resolve():
        raise ValueError("Summary JSON and Markdown must have distinct paths")
    if summary_path.exists() or markdown_path.exists():
        raise FileExistsError("Refusing to overwrite an existing baseline summary")
    summary = build_summary(review_path)
    markdown = render_summary(summary)
    for path in (summary_path, markdown_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(summary, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    with markdown_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(markdown)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=REVIEW_PATH)
    parser.add_argument("--json", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--markdown", type=Path, default=MARKDOWN_PATH)
    args = parser.parse_args()
    try:
        summary = write_report(args.review, args.json, args.markdown)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Report failed: {exc}")
        return 1
    print(json.dumps({key: {"value": value["value"], "eligible_count": value["eligible_count"]}
                      for key, value in summary["metrics"].items()}, indent=2))
    print(f"Saved summary: {args.json}, {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
