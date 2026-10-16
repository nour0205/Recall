"""Score Recall answers with RAGAS, and check RAGAS against the human labels.

Runs in its own environment (see evaluation/requirements-ragas.txt):

    .venv-ragas/Scripts/python -m evaluation.run_ragas run evaluation/results/<end_to_end run>.json
    .venv-ragas/Scripts/python -m evaluation.run_ragas calibrate

`run` scores a saved end-to-end run; `calibrate` scores the 76 human-labelled
Milestone 2 answers and compares each RAGAS metric with the matching human label
(see evaluation/ragas_data.py). Exact "I don't know." answers are skipped: they
make no claims, and refusal behaviour is already labelled deterministically.
Each run writes a new timestamped file to evaluation/results/. Calls the OpenAI API.
"""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
from statistics import mean

from evaluation import ragas_data
from evaluation.generation_benchmark import file_hash

RESULTS = Path("evaluation/results")
METRICS = ("faithfulness", "answer_relevancy", "context_recall", "factual_correctness")
# Which human label each metric is compared with during calibration.
HUMAN_MATCH = {"faithfulness": "groundedness", "factual_correctness": "correctness"}


def load_env(path=Path(".env")):
    if os.environ.get("OPENAI_API_KEY") or not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() == "OPENAI_API_KEY":
            os.environ["OPENAI_API_KEY"] = value.strip().strip('"')


def score(rows, grader: str):
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import EvaluationDataset, RunConfig, evaluate
    from ragas.cost import get_token_usage_for_openai
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import FactualCorrectness, Faithfulness, LLMContextRecall, ResponseRelevancy

    dataset = EvaluationDataset.from_list([
        {k: row[k] for k in ("user_input", "retrieved_contexts", "response", "reference")} for row in rows])
    result = evaluate(
        dataset,
        metrics=[Faithfulness(), ResponseRelevancy(), LLMContextRecall(), FactualCorrectness()],
        llm=LangchainLLMWrapper(ChatOpenAI(model=grader, temperature=0)),
        embeddings=LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small")),
        run_config=RunConfig(max_workers=8, timeout=180),
        token_usage_parser=get_token_usage_for_openai,
    )
    table = result.to_pandas()
    # Some columns carry the metric's settings, e.g. "factual_correctness(mode=f1)".
    columns = {m: next((c for c in table.columns if c == m or c.startswith(m + "(")), None) for m in METRICS}
    for row, (_, scored) in zip(rows, table.iterrows()):
        values = {m: (scored[c] if c is not None else None) for m, c in columns.items()}
        # Missing or NaN (a metric that failed on this answer) is recorded as None.
        row["scores"] = {m: (float(v) if v is not None and v == v else None) for m, v in values.items()}
    usage = result.total_tokens()
    return {"input_tokens": getattr(usage, "input_tokens", None), "output_tokens": getattr(usage, "output_tokens", None)}


def summary(rows) -> dict:
    means = {}
    for m in METRICS:
        values = [r["scores"][m] for r in rows if r["scores"].get(m) is not None]
        means[m] = {"mean": mean(values) if values else None, "scored": len(values), "missing": len(rows) - len(values)}
    return means


def main(mode: str, run_path: Path | None, grader: str):
    load_env()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if mode == "calibrate":
        from evaluation.run_judge import HUMAN_REVIEWS, calibration_cases
        rows, skipped = ragas_data.rows_from_calibration(calibration_cases())
        inputs = {name: {"path": p.as_posix(), "sha256": file_hash(p)} for name, p in HUMAN_REVIEWS.items()}
        output = RESULTS / f"ragas_calibration_{stamp}.json"
    else:
        rows, skipped = ragas_data.rows_from_run(run_path)
        inputs = {"run": {"path": Path(run_path).as_posix(), "sha256": file_hash(Path(run_path))}}
        output = RESULTS / f"ragas_{Path(run_path).stem}_{stamp}.json"
    if output.exists():
        raise FileExistsError(output)

    usage = score(rows, grader)
    report = {
        "result_schema_version": 1, "mode": mode, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": {"grader": grader, "embeddings": "text-embedding-3-small", "metrics": list(METRICS),
                          "ragas": version("ragas"), "langchain_openai": version("langchain-openai"),
                          "exact_refusals_skipped": True},
        "inputs": inputs, "token_usage": usage, "skipped_refusals": skipped,
        "summary": summary(rows),
        "rows": [{k: r[k] for k in r if k not in ("retrieved_contexts",)} for r in rows],
    }
    if mode == "calibrate":
        report["calibration"] = {m: ragas_data.calibrate(rows, m, h) for m, h in HUMAN_MATCH.items()}
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "token_usage": usage,
                      **({"calibration": report["calibration"]} if mode == "calibrate" else {})}, indent=2))
    print(f"Saved: {output}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["run", "calibrate"])
    parser.add_argument("run_path", type=Path, nargs="?")
    parser.add_argument("--grader", default="gpt-4o-mini", help="Model RAGAS uses to grade (default: gpt-4o-mini)")
    args = parser.parse_args()
    if args.mode == "run" and not args.run_path:
        parser.error("run needs the path of a saved end-to-end run")
    main(args.mode, args.run_path, args.grader)
