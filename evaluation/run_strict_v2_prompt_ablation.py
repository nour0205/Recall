"""One unscored, targeted strict-v2 pass over the unchanged frozen contexts."""
import json
from pathlib import Path

from evaluation import run_strict_prompt_ablation as frozen
from evaluation.run_balanced_prompt_ablation import efficiency
from evaluation.generation_benchmark import file_hash

PROMPT_VERSION = "grounded_strict_v2"
PROMPT_PATH = Path("evaluation/prompts/grounded_strict_v2.json")
OUTPUT_PATH = Path("evaluation/results/generation_strict_prompt_v2.json")
PRIOR_RUNS = {
    "grounded_strict_v1": Path("evaluation/results/generation_strict_prompt_v1.json"),
    "grounded_balanced_v2": Path("evaluation/results/generation_balanced_prompt_v2.json"),
}


def protected_hashes():
    paths = set(Path("evaluation/results").glob("*"))
    paths.difference_update({OUTPUT_PATH, OUTPUT_PATH.with_suffix(".json.checkpoint")})
    paths.update(Path("evaluation/prompts").glob("*.json"))
    return {**frozen.protected_hashes(), **{
        path.as_posix(): file_hash(path) for path in sorted(paths) if path.is_file()}}


def operational_summary(rows, baseline_rows):
    summary = frozen.operational_summary(rows, baseline_rows)
    summary.pop("answer_length_comparison")
    summary["efficiency_comparison"] = {
        "baseline": efficiency(baseline_rows),
        **{name: efficiency(json.loads(path.read_text(encoding="utf-8"))["queries"])
           for name, path in PRIOR_RUNS.items()},
        PROMPT_VERSION: efficiency(rows),
    }
    summary["comparison_note"] = "Operational efficiency only. Word counts use whitespace splits including Markdown/citations; no quality scoring or final quality comparison."
    return summary


def main(output_path=OUTPUT_PATH, client_factory=None):
    if Path(output_path).exists():
        raise FileExistsError("Refusing to overwrite or rerun an existing prompt ablation")
    _, _, baseline = frozen.frozen_inputs()
    for name, path in PRIOR_RUNS.items():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous["run_status"] != "completed" or len(previous["queries"]) != 19:
            raise ValueError("Expected completed prior experiment")
        if previous["configuration"] != {**baseline["configuration"], "prompt_version": name}:
            raise ValueError("Prior experiment settings differ from baseline")
        for old, row in zip(baseline["queries"], previous["queries"]):
            for field in ("question_id", "question", *frozen.CONTEXT_FIELDS):
                if old[field] != row[field]:
                    raise ValueError("Prior experiment differs from frozen baseline")
    return frozen.main(output_path, client_factory, prompt_path=PROMPT_PATH,
                       prompt_version=PROMPT_VERSION, protect=protected_hashes,
                       summarize=operational_summary)


if __name__ == "__main__":
    main()
