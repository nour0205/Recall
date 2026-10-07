"""One unscored balanced-prompt pass over frozen contexts; no retrieval."""
from pathlib import Path
import json
from statistics import mean

from evaluation import run_strict_prompt_ablation as frozen
from evaluation.generation_benchmark import file_hash

PROMPT_VERSION = "grounded_balanced_v2"
PROMPT_PATH = Path("evaluation/prompts/grounded_balanced_v2.json")
OUTPUT_PATH = Path("evaluation/results/generation_balanced_prompt_v2.json")
STRICT_PATH = Path("evaluation/results/generation_strict_prompt_v1.json")


def protected_hashes():
    paths = set(Path("evaluation/results").glob("*"))
    paths.discard(OUTPUT_PATH)
    paths.discard(OUTPUT_PATH.with_suffix(".json.checkpoint"))
    paths.update(Path("evaluation/prompts").glob("*.json"))
    return {**frozen.protected_hashes(), **{
        path.as_posix(): file_hash(path) for path in sorted(paths) if path.is_file()}}


def efficiency(rows):
    summary = frozen.operational_summary(rows, rows)
    answers = [row["generated_answer"] for row in rows if row["status"] == "completed"]
    return {"completed_generations": summary["completed_generations"],
            "generation_latency_seconds": summary["generation_latency_seconds"],
            "token_usage": summary["token_usage"],
            "mean_answer_characters": mean(map(len, answers)) if answers else None,
            "mean_answer_whitespace_words": mean(len(a.split()) for a in answers) if answers else None}


def operational_summary(rows, baseline_rows):
    strict = json.loads(STRICT_PATH.read_text(encoding="utf-8"))
    summary = frozen.operational_summary(rows, baseline_rows)
    summary.pop("answer_length_comparison")
    summary["efficiency_comparison"] = {
        "baseline": efficiency(baseline_rows),
        "grounded_strict_v1": efficiency(strict["queries"]),
        PROMPT_VERSION: efficiency(rows),
    }
    summary["comparison_note"] = "Measured operational efficiency only; lengths include citations/Markdown. No quality scoring."
    return summary


def main(output_path=OUTPUT_PATH, client_factory=None):
    if Path(output_path).exists():
        raise FileExistsError("Refusing to overwrite or rerun an existing prompt ablation")
    strict = json.loads(STRICT_PATH.read_text(encoding="utf-8"))
    _, _, baseline = frozen.frozen_inputs()
    if strict["run_status"] != "completed" or len(strict["queries"]) != 19:
        raise ValueError("Expected the completed strict experiment")
    if strict["configuration"] != {**baseline["configuration"], "prompt_version": "grounded_strict_v1"}:
        raise ValueError("Strict settings differ from baseline")
    for old, previous in zip(baseline["queries"], strict["queries"]):
        for field in ("question_id", "question", *frozen.CONTEXT_FIELDS):
            if old[field] != previous[field]:
                raise ValueError("Strict experiment differs from frozen baseline")
    return frozen.main(output_path, client_factory, prompt_path=PROMPT_PATH,
                       prompt_version=PROMPT_VERSION, protect=protected_hashes,
                       summarize=operational_summary)


if __name__ == "__main__":
    main()
