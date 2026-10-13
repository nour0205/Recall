"""LLM judge for Recall answers, using the Milestone 2 human-review rubric.

The judge sees exactly what a human reviewer saw: question, numbered sources,
answer, expected behavior, required points, reference answer and the benchmark
author's case notes. Human labels and reviewer notes never enter its input:
judge_input() builds the prompt from an explicit whitelist.
"""

import json
from pathlib import Path

from evaluation.generation_benchmark import REFERENCE_PATH, canonical_hash

PROMPT_PATH = Path("evaluation/prompts/judge_v1.json")
DIMENSIONS = ("correctness", "groundedness", "refusal_correctness", "citation_correctness")
_LABEL = {"enum": [0, 1, "N/A"]}
_BINARY = {"enum": [0, 1]}


def output_schema() -> dict:
    claim = {
        "type": "object", "additionalProperties": False,
        "required": ["claim", "supporting_sources", "supported", "cited_labels", "citation_supports_claim"],
        "properties": {
            "claim": {"type": "string"},
            "supporting_sources": {"type": "array", "items": {"type": "string"}},
            "supported": {"type": "boolean"},
            "cited_labels": {"type": "array", "items": {"type": "string"}},
            "citation_supports_claim": {"type": "boolean"},
        },
    }
    point = {
        "type": "object", "additionalProperties": False, "required": ["point_id", "judgment", "reason"],
        "properties": {"point_id": {"type": "string"}, "judgment": {"enum": ["pass", "fail"]}, "reason": {"type": "string"}},
    }
    return {
        "type": "object", "additionalProperties": False,
        "required": ["claims", "point_judgments", "correctness", "groundedness", "refusal_correctness",
                     "citation_correctness", "unsupported_claims", "citation_issues", "rationale"],
        "properties": {
            "claims": {"type": "array", "items": claim},
            "point_judgments": {"type": "array", "items": point},
            "correctness": _LABEL,
            "groundedness": _BINARY,
            "refusal_correctness": _LABEL,
            "citation_correctness": _LABEL,
            "unsupported_claims": {"type": "array", "items": {"type": "string"}},
            "citation_issues": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"},
        },
    }


def load_prompt(prompt_path=PROMPT_PATH, reference_path=REFERENCE_PATH) -> dict:
    prompt = json.loads(Path(prompt_path).read_text(encoding="utf-8"))
    rubric = json.loads(Path(reference_path).read_text(encoding="utf-8"))["rubric"]
    instructions = prompt["instructions"].replace("{rubric}", json.dumps(rubric, indent=2, ensure_ascii=False))
    return {**prompt, "instructions": instructions,
            "instructions_sha256": canonical_hash(instructions), "schema_sha256": canonical_hash(output_schema())}


def judge_input(case: dict) -> dict:
    """The only fields the judge may see. Labels and reviewer notes are excluded by construction."""
    sources = [{"label": f"[S{i}]", "document_id": chunk["document_id"], "text": chunk["text"]}
               for i, chunk in enumerate(case["sources"], 1)]
    return {
        "question": case["question"],
        "expected_behavior": case["expected_behavior"],
        "sources": sources,
        "answer": case["answer"],
        "required_points": [{"point_id": p["point_id"], "text": p["text"]} for p in case["required_points"]]
                           if case["expected_behavior"] == "answer" else [],
        "reference_answer": case["reference_answer"],
        "case_notes": case["case_notes"],
    }


def render_input(case: dict) -> str:
    data = judge_input(case)
    sources = "\n\n".join(f"{s['label']} DOCUMENT: {s['document_id']}\n{s['text']}" for s in data["sources"]) or "(none)"
    points = "\n".join(f"- {p['point_id']}: {p['text']}" for p in data["required_points"]) or "(none: refuse case)"
    return (f"QUESTION:\n{data['question']}\n\nEXPECTED BEHAVIOR: {data['expected_behavior']}\n\n"
            f"SUPPLIED SOURCES:\n{sources}\n\nGENERATED ANSWER:\n{data['answer']}\n\n"
            f"REQUIRED POINTS:\n{points}\n\nREFERENCE ANSWER:\n{data['reference_answer']}\n\n"
            f"CASE NOTES:\n{data['case_notes']}")


def validate_judgment(judgment: dict, case: dict) -> list[str]:
    """Checks the structured output against the case; returns problems (empty when valid)."""
    problems = []
    expected_points = [p["point_id"] for p in case["required_points"]] if case["expected_behavior"] == "answer" else []
    got_points = [p["point_id"] for p in judgment["point_judgments"]]
    if got_points != expected_points:
        problems.append(f"point_judgments {got_points} != required {expected_points}")
    if judgment["groundedness"] not in (0, 1):
        problems.append("groundedness must be 0 or 1")
    # Human convention: N/A only when an answerable question was answered (no refusal decision).
    answered = (case["answer"] or "").strip() != "I don't know."
    if judgment["refusal_correctness"] == "N/A" and not (case["expected_behavior"] == "answer" and answered):
        problems.append("refusal_correctness may be N/A only for an answered, answerable question")
    return problems


REFUSAL = "I don't know."


def refusal_labels(case: dict) -> dict:
    """Fixed rubric labels for an exact refusal, matching the Milestone 2 human review:
    a pure refusal makes no claims (correctness and citations N/A, grounded); it is a
    correct refusal on a refuse case and a false refusal that fails every point otherwise."""
    answerable = case["expected_behavior"] == "answer"
    return {
        "claims": [],
        "point_judgments": [{"point_id": p["point_id"], "judgment": "fail", "reason": "Refused an answerable question."}
                            for p in case["required_points"]] if answerable else [],
        "correctness": "N/A", "groundedness": 1, "citation_correctness": "N/A",
        "refusal_correctness": 0 if answerable else 1,
        "unsupported_claims": [], "citation_issues": [],
        "rationale": "Deterministic: exact refusal." + (" False refusal of an answerable question." if answerable else ""),
    }


def completeness_score(judgment: dict, case: dict):
    if case["expected_behavior"] != "answer":
        return "N/A"
    passed = sum(p["judgment"] == "pass" for p in judgment["point_judgments"])
    return passed / len(case["required_points"])


def judge(client, case: dict, prompt: dict) -> tuple[dict, dict]:
    response = client.chat.completions.create(
        model=prompt["model"],
        reasoning_effort=prompt["reasoning_effort"],
        messages=[{"role": "developer", "content": prompt["instructions"]},
                  {"role": "user", "content": render_input(case)}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "recall_judgment", "strict": True, "schema": output_schema()}},
    )
    judgment = json.loads(response.choices[0].message.content)
    meta = {"response_model": response.model, "response_id": response.id,
            "usage": response.usage.model_dump(mode="json") if response.usage else None}
    return judgment, meta
