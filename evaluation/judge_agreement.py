"""Agreement between judge and human labels. Pure functions; no I/O."""

from collections import Counter


def cohens_kappa(pairs) -> float | None:
    """Cohen's kappa for (human, judge) label pairs; None when undefined."""
    pairs = list(pairs)
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(h == j for h, j in pairs) / n
    human, judge = Counter(h for h, _ in pairs), Counter(j for _, j in pairs)
    expected = sum(human[label] * judge[label] for label in human) / (n * n)
    if expected == 1:
        return None  # Both raters used a single identical label: chance agreement is total.
    return (observed - expected) / (1 - expected)


def dimension_agreement(pairs) -> dict:
    pairs = [(h, j) for h, j in pairs]
    confusion = Counter(f"human={h} judge={j}" for h, j in pairs)
    agree = sum(h == j for h, j in pairs)
    return {
        "n": len(pairs),
        "agreement": f"{agree}/{len(pairs)}",
        "agreement_rate": agree / len(pairs) if pairs else None,
        "kappa": cohens_kappa(pairs),
        "confusion": dict(sorted(confusion.items())),
    }


def compare(cases) -> dict:
    """cases: dicts with 'human' and 'judge' label dicts plus point judgments.

    Each label dimension compares every case; "N/A" is treated as its own label,
    so a judge saying N/A where the human gave 0/1 counts as a disagreement.
    Completeness is compared point by point on answer cases.
    """
    report = {}
    for dimension in ("groundedness", "correctness", "citation_correctness", "refusal_correctness"):
        pairs = [(c["human"][dimension], c["judge"][dimension]) for c in cases]
        report[dimension] = dimension_agreement(pairs)
    point_pairs, score_errors = [], []
    for c in cases:
        human_points = {p["point_id"]: p["judgment"] for p in c["human"]["completeness_points"] or []}
        for p in c["judge"]["point_judgments"]:
            if human_points.get(p["point_id"]) in ("pass", "fail"):
                point_pairs.append((human_points[p["point_id"]], p["judgment"]))
        if c["expected_behavior"] == "answer":
            score_errors.append(abs(c["human"]["completeness_score"] - c["judge_completeness_score"]))
    report["completeness_points"] = dimension_agreement(point_pairs)
    report["completeness_score_mean_abs_error"] = sum(score_errors) / len(score_errors) if score_errors else None
    return report


def disagreements(cases) -> list[dict]:
    rows = []
    for c in cases:
        for dimension in ("groundedness", "correctness", "citation_correctness", "refusal_correctness"):
            if c["human"][dimension] != c["judge"][dimension]:
                rows.append({"run": c["run"], "question_id": c["question_id"], "dimension": dimension,
                             "human": c["human"][dimension], "judge": c["judge"][dimension]})
        human_points = {p["point_id"]: p["judgment"] for p in c["human"]["completeness_points"] or []}
        for p in c["judge"]["point_judgments"]:
            h = human_points.get(p["point_id"])
            if h in ("pass", "fail") and h != p["judgment"]:
                rows.append({"run": c["run"], "question_id": c["question_id"], "dimension": f"point:{p['point_id']}",
                             "human": h, "judge": p["judgment"], "judge_reason": p["reason"]})
    return rows
