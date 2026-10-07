"""Prepare and validate an unscored, offline human-review workspace.

No model calls, prompt changes, answer judging, aggregate metrics, or mutation of
the frozen inputs. Completed point labels are checked for arithmetic consistency;
the validator never writes or fills a reviewer field.
"""

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import re

from evaluation.generation_benchmark import (
    CASE_IDS, REFERENCE_PATH, RETRIEVAL_PATH, canonical_hash, file_hash,
    load_generation_benchmark,
)

BASELINE_PATH = Path("evaluation/results/generation_baseline_v1.json")
REVIEW_PATH = Path("evaluation/results/generation_baseline_v1_human_review.json")
SHEET_PATH = Path("evaluation/results/generation_baseline_v1_human_review.md")
STRICT_RUN_PATH = Path("evaluation/results/generation_strict_prompt_v1.json")
STRICT_PROMPT_PATH = Path("evaluation/prompts/grounded_strict_v1.json")
BALANCED_RUN_PATH = Path("evaluation/results/generation_balanced_prompt_v2.json")
BALANCED_PROMPT_PATH = Path("evaluation/prompts/grounded_balanced_v2.json")
STRICT_V2_RUN_PATH = Path("evaluation/results/generation_strict_prompt_v2.json")
STRICT_V2_PROMPT_PATH = Path("evaluation/prompts/grounded_strict_v2.json")
ABLATIONS = {
    "grounded_strict_v1": (STRICT_RUN_PATH, STRICT_PROMPT_PATH, "strict_prompt_definition_sha256"),
    "grounded_balanced_v2": (BALANCED_RUN_PATH, BALANCED_PROMPT_PATH, "prompt_definition_sha256"),
    "grounded_strict_v2": (STRICT_V2_RUN_PATH, STRICT_V2_PROMPT_PATH, "prompt_definition_sha256"),
}
LABEL_FIELDS = ("correctness", "groundedness", "refusal_correctness", "citation_correctness", "prompt_compliance")
LIST_FIELDS = ("unsupported_claims", "missing_required_points", "citation_issues")
REVIEWER_FIELDS = {*LABEL_FIELDS, *LIST_FIELDS, "completeness_points", "completeness_score",
                   "evidence_group_coverage", "reviewer_notes"}


def frozen_inputs(baseline_path=BASELINE_PATH, reference_path=REFERENCE_PATH, retrieval_path=RETRIEVAL_PATH):
    baseline_path, reference_path, retrieval_path = map(Path, (baseline_path, reference_path, retrieval_path))
    benchmark, references = load_generation_benchmark(reference_path, retrieval_path)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if baseline.get("run_status") != "completed" or not baseline.get("corpus_unchanged"):
        raise ValueError("Human review requires a completed baseline with unchanged corpus")
    if baseline.get("quality_scoring") != "not_performed":
        raise ValueError("Expected the frozen unscored baseline")
    if baseline.get("hashes", {}).get("generation_reference_sha256") != file_hash(reference_path):
        raise ValueError("Baseline/reference hash mismatch")
    if baseline.get("hashes", {}).get("retrieval_benchmark_sha256") != file_hash(retrieval_path):
        raise ValueError("Baseline/retrieval benchmark hash mismatch")
    rows = baseline.get("queries", [])
    if tuple(row.get("question_id") for row in rows) != CASE_IDS:
        raise ValueError("Baseline must have the exact 19 question IDs in frozen order")
    for case, ref, row in zip(benchmark.cases, references.cases, rows):
        if row.get("status") != "completed" or not isinstance(row.get("generated_answer"), str):
            raise ValueError(f"{case.question_id}: incomplete generation")
        if row.get("question") != case.question or row.get("expected_behavior") != ref.expected_behavior:
            raise ValueError(f"{case.question_id}: question/behavior mismatch")
        if any(value is not None for value in row.get("human_evaluation", {}).values()):
            raise ValueError("The raw baseline must remain unscored")
        chunks = row.get("retrieved_context_chunks", [])
        mapping = {f"[S{i}]": {"chunk_id": chunk["chunk_id"], "document_id": chunk["document_id"],
                               "context_position": i} for i, chunk in enumerate(chunks, 1)}
        if len(chunks) != 5 or row.get("source_mapping") != mapping:
            raise ValueError(f"{case.question_id}: invalid frozen top-five source mapping")
        for i, chunk in enumerate(chunks, 1):
            if chunk.get("source_label") != f"[S{i}]" or chunk.get("context_position") != i:
                raise ValueError(f"{case.question_id}: source order mismatch")
        if row.get("prompt_sha256") != canonical_hash(row.get("prompt_messages")):
            raise ValueError(f"{case.question_id}: prompt hash mismatch")
        if case.answerable and row.get("context_sufficient_for_full_answer") is not True:
            raise ValueError(f"{case.question_id}: expected confirmed sufficient context")
    return benchmark, references, baseline


def review_inputs(run_path=None, baseline_path=BASELINE_PATH, reference_path=REFERENCE_PATH, retrieval_path=RETRIEVAL_PATH):
    """Select saved answers while enforcing the same frozen baseline evidence.

    This is a file-only adapter. It neither imports a generator nor evaluates
    answer quality. Baseline callers retain their original defaults and schema.
    """
    benchmark, references, baseline = frozen_inputs(baseline_path, reference_path, retrieval_path)
    if run_path is None or Path(run_path).resolve() == Path(baseline_path).resolve():
        return benchmark, references, baseline
    strict = json.loads(Path(run_path).read_text(encoding="utf-8"))
    prompt_version = strict.get("configuration", {}).get("prompt_version")
    if prompt_version not in ABLATIONS:
        raise ValueError("Unknown evaluation prompt version")
    _, prompt_path, prompt_hash_key = ABLATIONS[prompt_version]
    if strict.get("run_status") != "completed" or strict.get("protected_files_unchanged") is not True:
        raise ValueError("Strict review requires a completed run with unchanged protected inputs")
    if strict.get("quality_scoring") != "not_performed" or strict.get("retrieval_executed") is not False:
        raise ValueError("Strict run must be unscored and reuse frozen retrieval")
    if strict.get("hashes", {}).get("frozen_baseline_sha256") != file_hash(Path(baseline_path)):
        raise ValueError("Strict run/frozen baseline hash mismatch")
    for name, path in (("generation_reference_sha256", reference_path), ("retrieval_benchmark_sha256", retrieval_path),
                       (prompt_hash_key, prompt_path)):
        if strict.get("hashes", {}).get(name) != file_hash(Path(path)):
            raise ValueError(f"Strict run/{name} mismatch")
    definition = json.loads(prompt_path.read_text(encoding="utf-8"))
    if definition.get("prompt_version") != prompt_version or strict.get("prompt_definition") != definition:
        raise ValueError("Strict prompt definition mismatch")
    if strict.get("configuration") != {**baseline["configuration"], "prompt_version": prompt_version}:
        raise ValueError("Strict run changed settings beyond the prompt")
    rows = strict.get("queries", [])
    if tuple(row.get("question_id") for row in rows) != CASE_IDS:
        raise ValueError("Strict run must preserve all 19 frozen question IDs and ordering")
    fixed_fields = ("question_id", "question", "expected_behavior", "retrieved_context_chunks", "retrieved_chunk_ids",
                    "source_mapping", "required_point_evidence", "context_sufficient_for_full_answer",
                    "model", "temperature", "max_tokens", "retrieval_mode", "retrieval_algorithm", "top_k", "candidate_k")
    for original, row in zip(baseline["queries"], rows):
        qid = original["question_id"]
        if row.get("status") != "completed" or not isinstance(row.get("generated_answer"), str) or not row["generated_answer"]:
            raise ValueError(f"{qid}: incomplete strict generation")
        if any(canonical_hash(row.get(field)) != canonical_hash(original[field]) for field in fixed_fields):
            raise ValueError(f"{qid}: strict evidence, question, or settings differ from baseline")
        if row.get("prompt_version") != prompt_version or row.get("retrieval_executed") is not False:
            raise ValueError(f"{qid}: invalid strict prompt metadata")
        if any(value is not None for value in row.get("human_evaluation", {}).values()):
            raise ValueError("The strict raw outputs must remain unscored")
        context = "\n\n".join(f"{chunk['source_label']} DOCUMENT: {chunk['document_id']}\nCONTENT:\n{chunk['text']}"
                               for chunk in row["retrieved_context_chunks"])
        messages = [{"role": "system", "content": definition["system"]},
                    {"role": "user", "content": definition["user_template"].format(context=context, question=row["question"])}]
        if row.get("prompt_messages") != messages or row.get("prompt_sha256") != canonical_hash(messages):
            raise ValueError(f"{qid}: strict prompt messages/hash mismatch")
    return benchmark, references, strict


def create_workspace(baseline_path=BASELINE_PATH, reference_path=REFERENCE_PATH, retrieval_path=RETRIEVAL_PATH, *, run_path=None):
    _, references, baseline = review_inputs(run_path, baseline_path, reference_path, retrieval_path)
    cases = []
    for ref, raw in zip(references.cases, baseline["queries"]):
        cases.append({
            "question_id": raw["question_id"], "question": raw["question"],
            "expected_behavior": ref.expected_behavior, "reference_answer": ref.reference_answer,
            "required_points": [point.model_dump(exclude_none=True) for point in ref.required_points],
            "retrieved_context_sufficient": raw["context_sufficient_for_full_answer"],
            "required_point_evidence": deepcopy(raw["required_point_evidence"]),
            "retrieved_context_chunks": deepcopy(raw["retrieved_context_chunks"]),
            "source_mapping": deepcopy(raw["source_mapping"]),
            "generated_answer": raw["generated_answer"],
            "forbidden_or_unsupported_points": list(ref.forbidden_or_unsupported_points),
            "citation_expectation": ref.citation_expectation.model_dump(),
            "reference_review_notes": ref.review_notes,
            **dict.fromkeys(LABEL_FIELDS),
            "completeness_points": [{"point_id": point.point_id, "judgment": None} for point in ref.required_points],
            "completeness_score": None, "evidence_group_coverage": None,
            "unsupported_claims": [], "missing_required_points": [], "citation_issues": [],
            "reviewer_notes": "",
        })
    workspace = {
        "schema_version": 1, "review_status": "draft",
        "source_artifacts": {
            name: {"path": Path(path).as_posix(), "sha256": file_hash(Path(path))}
            for name, path in (("baseline", baseline_path), ("references", reference_path), ("retrieval", retrieval_path))
        },
        "instructions": {
            "labels": "Use integer 0/1 or the string N/A; groundedness is 0/1 only. Null means unreviewed.",
            "points": "Use pass/fail/null for each required-point judgment; preserve point IDs and order.",
            "completeness": "Answer cases: enter pass count / full required-point count; do not shrink the denominator. Refusal cases: enter N/A for completeness_score and evidence_group_coverage when finalizing.",
            "groups": "Answer cases: replace null evidence_group_coverage with an object mapping every evidence_group_id to 0/1. A group is 1 only when all its mapped points pass.",
            "finalization": "Set review_status to finalized only when mandatory labels are complete. Prompt compliance is an optional dimension: enter N/A if skipped. Refusal-case behavioral point judgments may remain null; refusal_correctness captures the decision.",
            "missing_points": "For answer cases, missing_required_points must list the point IDs judged fail when finalizing. An incorrect point also fails completeness.",
            "issues": "unsupported_claims and citation_issues contain reviewer-written strings; reviewer_notes is free text. No score or issue is inferred automatically.",
            "provenance": "Edit reviewer fields only. Exact questions, references, answers, context, source mapping, rubric, and source hashes are validated against frozen inputs.",
        },
        "rubric": deepcopy(references.rubric), "cases": cases,
    }
    if run_path is not None and Path(run_path).resolve() != Path(baseline_path).resolve():
        # Prompt/run metadata stays in the existing provenance field; case and
        # reviewer schemas, instructions, and rubric are identical to baseline.
        workspace["source_artifacts"]["generation_run"] = {
            "path": Path(run_path).as_posix(), "sha256": file_hash(Path(run_path)),
            "prompt_version": baseline["configuration"]["prompt_version"],
        }
        workspace["source_artifacts"]["prompt"] = {
            "path": ABLATIONS[baseline["configuration"]["prompt_version"]][1].as_posix(),
            "sha256": file_hash(ABLATIONS[baseline["configuration"]["prompt_version"]][1]),
            "prompt_version": baseline["configuration"]["prompt_version"],
        }
    return workspace


def _label(value, field, finalized, errors):
    if value is None and not finalized:
        return
    if type(value) is int and value in (0, 1):
        return
    if field != "groundedness" and value == "N/A" and type(value) is str:
        return
    errors.append(f"{field}: expected integer 0/1" + (" or N/A" if field != "groundedness" else ""))


def _fraction(value):
    return type(value) in (int, float) and 0 <= value <= 1 and math.isfinite(value)


def validate_workspace(workspace, *, finalized=False, baseline_path=BASELINE_PATH,
                       reference_path=REFERENCE_PATH, retrieval_path=RETRIEVAL_PATH, run_path=None):
    """Return actionable errors; never infer labels, mutate data, or aggregate.

--finalized or review_status=finalized applies strict completion checks. Draft
mode still rejects any invalid non-null labels and changes to frozen content.
"""
    if run_path is None and isinstance(workspace, dict) and isinstance(workspace.get("source_artifacts"), dict):
        if "generation_run" in workspace["source_artifacts"]:
            metadata = workspace["source_artifacts"]["generation_run"]
            run_path = ABLATIONS.get(metadata.get("prompt_version"), ABLATIONS["grounded_strict_v1"])[0]
    expected = create_workspace(baseline_path, reference_path, retrieval_path, run_path=run_path)
    errors = []
    if not isinstance(workspace, dict):
        return ["Workspace must be a JSON object"]
    if workspace.keys() != expected.keys():
        errors.append("Workspace fields differ from the schema")
    if workspace.get("review_status") not in ("draft", "finalized"):
        errors.append("review_status must be draft or finalized")
    finalized = finalized or workspace.get("review_status") == "finalized"
    for field in ("schema_version", "source_artifacts", "instructions", "rubric"):
        if canonical_hash(workspace.get(field)) != canonical_hash(expected[field]):
            errors.append(f"{field}: frozen provenance/schema/instructions changed")
    cases = workspace.get("cases")
    if not isinstance(cases, list) or any(not isinstance(case, dict) for case in cases):
        return errors + ["cases must be an array of objects"]
    if tuple(case.get("question_id") for case in cases) != CASE_IDS:
        return errors + ["cases must contain the exact 19 IDs in frozen order, preserving the 018 gap"]
    for row, source in zip(cases, expected["cases"]):
        prefix = row["question_id"] + ": "
        issues = []
        if row.keys() != source.keys():
            issues.append("Case fields differ from the schema")
        for field in source.keys() - REVIEWER_FIELDS:
            if canonical_hash(row.get(field)) != canonical_hash(source[field]):
                issues.append(f"{field}: frozen content changed")
        for field in LABEL_FIELDS:
            _label(row.get(field), field, finalized, issues)
        if not isinstance(row.get("reviewer_notes"), str):
            issues.append("reviewer_notes must be a string")
        for field in LIST_FIELDS:
            values = row.get(field)
            if not isinstance(values, list) or any(not isinstance(item, str) or not item.strip() for item in values):
                issues.append(f"{field} must be an array of nonempty strings")
        points = row.get("completeness_points")
        expected_ids = [point["point_id"] for point in source["required_points"]]
        points_valid = isinstance(points, list) and all(isinstance(point, dict) for point in points)
        if not points_valid or [point.get("point_id") for point in points] != expected_ids:
            issues.append("completeness_points must contain every required-point ID exactly once in order")
            points_valid = False
        if points_valid:
            for point in points:
                if point.keys() != {"point_id", "judgment"}:
                    issues.append("Point judgments require only point_id and judgment")
                judgment = point.get("judgment")
                if judgment is not None and (type(judgment) is not str or judgment not in ("pass", "fail")):
                    issues.append(f"{point['point_id']}: judgment must be pass/fail/null")
                    points_valid = False
                if finalized and source["expected_behavior"] == "answer" and judgment is None:
                    issues.append(f"{point['point_id']}: missing required-point judgment")
        score = row.get("completeness_score")
        coverage = row.get("evidence_group_coverage")
        answerable = source["expected_behavior"] == "answer"
        groups = sorted({gid for point in source["required_points"] for gid in point["evidence_group_ids"]})
        if answerable:
            if not (score is None and not finalized) and not _fraction(score):
                issues.append("completeness_score must be a finite number between 0 and 1")
            coverage_valid = isinstance(coverage, dict) and set(coverage) == set(groups)
            if coverage_valid:
                coverage_valid = all(type(value) is int and value in (0, 1) for value in coverage.values())
            if not (coverage is None and not finalized) and not coverage_valid:
                issues.append("evidence_group_coverage must map every evidence group to integer 0/1")
            if points_valid and all(point.get("judgment") in ("pass", "fail") for point in points):
                judgments = {point["point_id"]: point["judgment"] for point in points}
                # Check manually-entered values only; never assign these calculations.
                if _fraction(score) and not math.isclose(score, sum(value == "pass" for value in judgments.values()) / len(points), rel_tol=0, abs_tol=1e-9):
                    issues.append("completeness_score disagrees with required-point judgments")
                if coverage_valid:
                    for gid in groups:
                        group_pass = all(judgments[p["point_id"]] == "pass" for p in source["required_points"] if gid in p["evidence_group_ids"])
                        if coverage[gid] != int(group_pass):
                            issues.append(f"evidence_group_coverage.{gid} disagrees with mapped point judgments")
                missing = row.get("missing_required_points")
                failed = {pid for pid, judgment in judgments.items() if judgment == "fail"}
                if finalized and isinstance(missing, list) and all(isinstance(pid, str) for pid in missing) and (set(missing) != failed or len(missing) != len(failed)):
                    issues.append("missing_required_points must list exactly the failed required-point IDs")
        else:
            if not (score is None and not finalized) and score != "N/A":
                issues.append("Refusal-case completeness_score must be N/A")
            if not (coverage is None and not finalized) and coverage != "N/A":
                issues.append("Refusal-case evidence_group_coverage must be N/A")
        if isinstance(row.get("missing_required_points"), list):
            if any(pid not in expected_ids for pid in row["missing_required_points"]):
                issues.append("missing_required_points contains an unknown point ID")
        errors.extend(prefix + issue for issue in issues)
    return errors


def fenced(text):
    """Literal Markdown block with a fence that cannot collide with its content."""
    longest = max((len(match.group()) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}text\n{text}" + ("" if text.endswith("\n") else "\n") + fence


def render_sheet(workspace, review_filename=None):
    run = workspace["source_artifacts"].get("generation_run")
    source_path = Path(run["path"] if run else workspace["source_artifacts"]["baseline"]["path"])
    title = f"{run['prompt_version']} — Human Review" if run else "Generation Baseline v1 — Human Review"
    review_filename = review_filename or source_path.stem + "_human_review.json"
    review_path = source_path.with_name(review_filename).as_posix()
    validation_target = f" {review_path}" if run else ""
    lines = [
        f"# {title}", "",
        "All reviewer fields are blank. Edit the companion JSON for machine validation; this sheet is an inspection aid.", "",
        f"[Editable review JSON]({review_filename}) · [Frozen {'generation run' if run else 'baseline'}]({source_path.name}) · [References and rubric](../benchmarks/generation_reference_v1.json)", "",
        "Use `0`, `1`, or `N/A`; groundedness permits only `0`/`1`. Point judgments are `pass`/`fail`. Null means unreviewed.", "",
        "References are synthesis examples, not exact-match targets. Groundedness and citation support use only the exact supplied context below.", "",
        "For answer cases, enter completeness as passed points / all required points and group coverage as `{group_id: 0/1}`. A group passes only when all mapped points pass. Refusal-case completeness and group coverage are `N/A`; prompt compliance may be skipped with `N/A`.", "",
        f"Validate drafts: `python -m evaluation.generation_human_review validate{validation_target}`", "",
        f"Validate completed labels: `python -m evaluation.generation_human_review validate{validation_target} --finalized`", "",
        "<details><summary>Scoring rubric and handling rules</summary>", "",
    ]
    for dimension, spec in workspace["rubric"].items():
        if dimension != "handling_rules":
            lines.extend([f"- **{dimension}**: {spec['rule']}"])
    lines.append("")
    lines.extend(f"- {rule}" for rule in workspace["rubric"]["handling_rules"])
    lines.extend(["", "</details>", ""])
    if run:
        prompt_path = ABLATIONS[run["prompt_version"]][1]
        prompt = json.loads(prompt_path.read_text(encoding="utf-8"))
        lines.extend([f"**Prompt version:** `{run['prompt_version']}` · [Exact prompt definition](../prompts/{prompt_path.name})", "",
                      "The scoring rubric is unchanged. Assess prompt compliance against this run's strict prompt.", "",
                      "<details><summary>Strict system prompt and user template — verbatim</summary>", "",
                      fenced(prompt["system"]), "", fenced(prompt["user_template"]), "", "</details>", ""])
    for row in workspace["cases"]:
        sufficiency = "not applicable (refusal case)" if row["retrieved_context_sufficient"] is None else str(row["retrieved_context_sufficient"]).lower()
        lines.extend([f"## {row['question_id']}", "", f"**Question:** {row['question']}", "",
                      f"**Expected behavior:** `{row['expected_behavior']}` · **Retrieved context sufficient:** {sufficiency}", "",
                      f"**Reference answer:** {row['reference_answer']}", "", "**Required points**", ""])
        for point in row["required_points"]:
            groups = ", ".join(point["evidence_group_ids"]) or "behavioral; no evidence group"
            lines.append(f"- `{point['point_id']}`: {point['text']} (groups: `{groups}`)")
        if row["forbidden_or_unsupported_points"]:
            lines.extend(["", "**Unsupported-content guardrails**", ""])
            lines.extend(f"- {point}" for point in row["forbidden_or_unsupported_points"])
        lines.extend(["", f"**Reference review note:** {row['reference_review_notes']}", "",
                      "<details><summary>Exact retrieved context — five sources in prompt order</summary>", ""])
        for context in row["retrieved_context_chunks"]:
            label = context["source_label"]
            lines.extend([f"**{label}** · document `{context['document_id']}` · chunk `{context['chunk_id']}`", ""])
            metadata = context["metadata"]
            visible = {key: metadata[key] for key in ("source", "owner", "course", "chunk_index") if key in metadata}
            if visible:
                lines.extend(["Metadata: " + json.dumps(visible, ensure_ascii=False, sort_keys=True), ""])
            lines.extend([fenced(context["text"]), ""])
        lines.extend(["</details>", "", "**Generated answer — verbatim**", "", fenced(row["generated_answer"]), "",
                      "**Blank scoring checklist**", "",
                      "| Dimension | Human label |", "| --- | --- |"])
        lines.extend(f"| {field} | |" for field in LABEL_FIELDS)
        lines.extend(["| completeness_score | |", "| evidence_group_coverage | |", "",
                      "| Required point | pass / fail |", "| --- | --- |"])
        lines.extend(f"| {point['point_id']} | |" for point in row["required_points"])
        lines.extend(["", "- [ ] unsupported_claims: __________", "- [ ] missing_required_points: __________",
                      "- [ ] citation_issues: __________", "- [ ] reviewer_notes: __________", ""])
    return "\n".join(lines)


def prepare(review_path=REVIEW_PATH, sheet_path=SHEET_PATH, *, run_path=None):
    review_path, sheet_path = Path(review_path), Path(sheet_path)
    if review_path.resolve() == sheet_path.resolve():
        raise ValueError("Review JSON and Markdown must have distinct paths")
    if review_path.exists() or sheet_path.exists():
        raise FileExistsError("Refusing to overwrite an existing human-review workspace")
    # Do not allow output paths to overwrite any frozen input.
    inputs = {path.resolve() for path in (BASELINE_PATH, REFERENCE_PATH, RETRIEVAL_PATH, STRICT_RUN_PATH, STRICT_PROMPT_PATH,
                                        BALANCED_RUN_PATH, BALANCED_PROMPT_PATH, STRICT_V2_RUN_PATH, STRICT_V2_PROMPT_PATH)}
    if review_path.resolve() in inputs or sheet_path.resolve() in inputs:
        raise ValueError("Human-review outputs must not target frozen inputs")
    workspace = create_workspace(run_path=run_path)
    errors = validate_workspace(workspace, run_path=run_path)
    if errors:
        raise ValueError("\n".join(errors))
    sheet = render_sheet(workspace, review_filename=review_path.name)
    for path in (review_path, sheet_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    with review_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(workspace, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    with sheet_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(sheet)
    return review_path, sheet_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare", help="Create blank JSON and Markdown; never overwrite")
    prepare_parser.add_argument("--review", type=Path, default=REVIEW_PATH)
    prepare_parser.add_argument("--sheet", type=Path, default=SHEET_PATH)
    prepare_parser.add_argument("--run", type=Path, help="Reuse the frozen strict-prompt run; default is baseline")
    validation_parser = commands.add_parser("validate", help="Read-only validation; no score filling or aggregation")
    validation_parser.add_argument("path", nargs="?", type=Path, default=REVIEW_PATH)
    validation_parser.add_argument("--finalized", action="store_true")
    validation_parser.add_argument("--run", type=Path, help="Explicit run source; strict review provenance is detected by default")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            paths = prepare(args.review, args.sheet, run_path=args.run)
            print("Created blank human-review workspace: " + ", ".join(str(path) for path in paths))
        else:
            workspace = json.loads(args.path.read_text(encoding="utf-8"))
            errors = validate_workspace(workspace, finalized=args.finalized, run_path=args.run)
            if errors:
                print("\n".join(errors))
                return 1
            mode = "finalized" if args.finalized or workspace["review_status"] == "finalized" else "draft"
            print(f"Valid {mode} review: 19 cases; no scores filled or aggregate metrics calculated.")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Validation/preparation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
