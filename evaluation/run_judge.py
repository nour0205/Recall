"""Run the LLM judge. Two modes, each writing a new timestamped result file:

    python -m evaluation.run_judge [--prompt evaluation/prompts/judge_v2.json] calibrate
        Judge the 76 human-reviewed Milestone 2 answers (4 prompts x 19 cases)
        and report agreement with the human labels per dimension.

    python -m evaluation.run_judge end-to-end evaluation/results/end_to_end_v1_<...>.json
        Judge the answers from an end-to-end run of the production /ask path.

The judge never sees human labels or reviewer notes (see evaluation/judge.py).
Existing result files are never overwritten. Both modes call the OpenAI API.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import threading

from evaluation import judge as judge_lib
from evaluation.generation_benchmark import REFERENCE_PATH, file_hash
from evaluation.judge_agreement import compare, disagreements

RESULTS = Path("evaluation/results")
HUMAN_REVIEWS = {
    "baseline": RESULTS / "generation_baseline_v1_human_review.json",
    "strict_v1": RESULTS / "generation_strict_prompt_v1_human_review.json",
    "balanced_v2": RESULTS / "generation_balanced_prompt_v2_human_review.json",
    "strict_v2": RESULTS / "generation_strict_prompt_v2_human_review.json",
}
HUMAN_FIELDS = ("correctness", "groundedness", "refusal_correctness", "citation_correctness",
                "completeness_points", "completeness_score")
WORKERS = 6
DEFAULT_PROMPT = Path("evaluation/prompts/judge_v2.json")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def calibration_cases() -> list[dict]:
    cases = []
    for run, path in HUMAN_REVIEWS.items():
        review = json.loads(path.read_text(encoding="utf-8"))
        if review["review_status"] != "finalized":
            raise ValueError(f"{path} is not finalized")
        for c in review["cases"]:
            cases.append({
                "run": run, "question_id": c["question_id"], "question": c["question"],
                "expected_behavior": c["expected_behavior"],
                "sources": [{"document_id": ch["document_id"], "text": ch["text"]} for ch in c["retrieved_context_chunks"]],
                "answer": c["generated_answer"], "required_points": c["required_points"],
                "reference_answer": c["reference_answer"], "case_notes": c["reference_review_notes"],
                "human": {field: c[field] for field in HUMAN_FIELDS},
            })
    return cases


def end_to_end_cases(run_path: Path) -> list[dict]:
    run = json.loads(run_path.read_text(encoding="utf-8"))
    # Runs on a quote-based benchmark (v3 draft) record it in their provenance.
    benchmark = (run.get("provenance") or {}).get("benchmark") or ""
    source = Path(benchmark) if Path(benchmark).name.startswith("benchmark_v3") else REFERENCE_PATH
    references = {c["question_id"]: c for c in json.loads(source.read_text(encoding="utf-8"))["cases"]}
    cases = []
    for row in run["queries"]:
        reference = references[row["question_id"]]
        # The context the answer prompt saw: retrieved chunks with text, in [S#] order.
        context = [c for c in row["retrieved_context"] or [] if c["text"].strip()]
        cases.append({
            "run": "end_to_end", "question_id": row["question_id"], "question": row["question"],
            "expected_behavior": row["expected_behavior"],
            "sources": [{"document_id": c["document_id"], "text": c["text"]} for c in context],
            "answer": row["answer"], "required_points": reference["required_points"],
            "reference_answer": reference["reference_answer"], "case_notes": reference["review_notes"],
        })
    return cases


def judge_all(cases, client, prompt, report, output_path, deterministic_refusals=False):
    lock = threading.Lock()

    def one(case):
        if deterministic_refusals and (case["answer"] or "").strip() == judge_lib.REFUSAL:
            judgment = judge_lib.refusal_labels(case)
            row = {**case, "judge": judgment, "judge_meta": {"deterministic": True}, "judge_problems": [],
                   "judge_completeness_score": judge_lib.completeness_score(judgment, case)}
            with lock:
                report["judgments"].append(row)
                save(output_path, report)
            return
        try:
            judgment, meta = judge_lib.judge(client, case, prompt)
            problems = judge_lib.validate_judgment(judgment, case)
            row = {**case, "judge": judgment, "judge_meta": meta, "judge_problems": problems,
                   "judge_completeness_score": judge_lib.completeness_score(judgment, case)}
        except Exception as exc:  # Recorded, never retried automatically.
            row = {**case, "judge": None, "judge_error": {"type": type(exc).__name__,
                                                          "status_code": getattr(exc, "status_code", None)}}
        with lock:
            report["judgments"].append(row)
            save(output_path, report)
            status = "ok" if row.get("judge") and not row.get("judge_problems") else "PROBLEM"
            print(f"{row['run']:>11} {row['question_id']}: {status}", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(one, cases))
    order = {(c["run"], c["question_id"]): i for i, c in enumerate(cases)}
    report["judgments"].sort(key=lambda r: order[(r["run"], r["question_id"])])


def usable(rows):
    return [r for r in rows if r.get("judge") and not r.get("judge_problems")]


def end_to_end_summary(rows) -> dict:
    good = usable(rows)
    answer = [r for r in good if r["expected_behavior"] == "answer"]
    count = lambda rs, dim, value=1: f"{sum(r['judge'][dim] == value for r in rs)}/{len(rs)}"
    return {
        "judged": f"{len(good)}/{len(rows)}",
        "groundedness": count(good, "groundedness"),
        "correctness_answer_cases": count(answer, "correctness"),
        "citation_correctness_answer_cases": count(answer, "citation_correctness"),
        "refusal_correctness": count([r for r in good if r["judge"]["refusal_correctness"] != "N/A"], "refusal_correctness"),
        "mean_completeness": (sum(r["judge_completeness_score"] for r in answer) / len(answer)) if answer else None,
        "completeness_sum": f"{sum(r['judge_completeness_score'] for r in answer):g}/{len(answer)}",
    }


def save(path: Path, report: dict):
    temporary = path.with_suffix(path.suffix + ".checkpoint")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def main(mode: str, run_path: Path | None = None, prompt_path: Path = DEFAULT_PROMPT, deterministic_refusals: bool = False):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prompt = judge_lib.load_prompt(prompt_path)
    kind = "calibration" if mode == "calibrate" else "end_to_end"
    output_path = RESULTS / f"judge_{kind}_{prompt['prompt_id']}_{stamp}.json"
    if output_path.exists():
        raise FileExistsError(output_path)
    cases = calibration_cases() if mode == "calibrate" else end_to_end_cases(run_path)
    sources = {name: {"path": p.as_posix(), "sha256": file_hash(p)} for name, p in HUMAN_REVIEWS.items()} \
        if mode == "calibrate" else {"end_to_end_run": {"path": run_path.as_posix(), "sha256": file_hash(run_path)}}

    from openai import OpenAI
    from app.config import OPENAI_API_KEY

    report = {
        "result_schema_version": 1, "mode": mode, "run_status": "running",
        "started_at_utc": utc_now(), "completed_at_utc": None,
        "judge": {"prompt_id": prompt["prompt_id"], "model": prompt["model"],
                  "reasoning_effort": prompt["reasoning_effort"], "instructions_sha256": prompt["instructions_sha256"],
                  "schema_sha256": prompt["schema_sha256"], "prompt_path": Path(prompt_path).as_posix(), "prompt_file_sha256": file_hash(Path(prompt_path)),
                  "reference_sha256": file_hash(REFERENCE_PATH), "deterministic_refusals": deterministic_refusals},
        "inputs": sources, "judgments": [], "summary": None,
    }
    with output_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream)
    client = OpenAI(api_key=OPENAI_API_KEY, max_retries=2, timeout=300)
    try:
        judge_all(cases, client, prompt, report, output_path, deterministic_refusals)
        good = usable(report["judgments"])
        if mode == "calibrate":
            report["summary"] = {"judged": f"{len(good)}/{len(cases)}", "agreement": compare(good),
                                 "per_run": {run: compare([r for r in good if r["run"] == run]) for run in HUMAN_REVIEWS}}
            report["disagreements"] = disagreements(good)
        else:
            report["summary"] = end_to_end_summary(report["judgments"])
        report["run_status"] = "completed" if len(good) == len(cases) else "completed_with_problems"
    except BaseException:
        report["run_status"] = "interrupted"
        raise
    finally:
        report["completed_at_utc"] = utc_now()
        save(output_path, report)
        client.close()
    print(json.dumps(report["summary"] if mode != "calibrate" else report["summary"]["agreement"], indent=2), flush=True)
    print(f"Saved: {output_path}", flush=True)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT, help="Judge prompt file (default: judge_v2)")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("calibrate")
    e2e = sub.add_parser("end-to-end")
    e2e.add_argument("run_path", type=Path)
    e2e.add_argument("--deterministic-refusals", action="store_true",
                     help="Label exact \"I don't know.\" answers with the rubric's fixed refusal labels, without a model call")
    args = parser.parse_args()
    main(args.mode, getattr(args, "run_path", None), args.prompt, getattr(args, "deterministic_refusals", False))
