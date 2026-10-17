#!/usr/bin/env python3
"""Summarize a human review rubric without changing project state.

apply_dim_weights and summarize_scores adapted from rootkiller6788/mathmodel-skill,
commit a5f4d60c7db2a98e1284b1995a1aaaaa008facd5, scripts/score_artifact.py.
Copyright (c) 2026 rootkiller6788; Copyright (c) 2026 handsomeZR-netizen.
See licenses/ and THIRD_PARTY_NOTICES.md for complete MIT notices.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

DIMENSIONS = (
    "topic", "literature", "design", "fieldwork", "analysis", "report", "innovation"
)
WEIGHT_CLAMP_MIN = 0.7
WEIGHT_CLAMP_MAX = 1.5


def apply_dim_weights(scores: dict, weights_for_stage: dict) -> dict:
    """
    weighted_score[dim] = clamp(weight, [WEIGHT_CLAMP_MIN, WEIGHT_CLAMP_MAX]).
    返回 {dim: weight} (1.0 if not in table); 给 compute_verdict 用.

    分离 weight 与 score 是为了:
    - 加权 mean = sum(score * weight) / sum(weight)
    - 加权 min = min(score) (不加权, 仍用作 'any dim too low' 触发)
    """
    out = {}
    for dim_name in scores:
        w = weights_for_stage.get(dim_name, 1.0)
        w_clamped = max(WEIGHT_CLAMP_MIN, min(WEIGHT_CLAMP_MAX, w))
        out[dim_name] = w_clamped
    return out


def summarize_scores(scores: dict, weights_for_stage: dict = None) -> dict:
    """Return one canonical score summary used by validation, verdicts, and logs."""
    score_values = {k: d["score"] for k, d in scores.items()}
    raw_min = min(score_values.values())
    raw_mean = sum(score_values.values()) / len(score_values)

    w_table = apply_dim_weights(score_values, weights_for_stage or {})
    weight_total = sum(w_table.values())
    weighted_mean = (
        sum(score_values[d] * w_table[d] for d in score_values) / weight_total
        if weight_total else raw_mean
    )
    return {
        "raw_min": raw_min,
        "raw_mean": raw_mean,
        "weighted_mean": weighted_mean,
        "weights": w_table,
    }


def validate_review(data: dict) -> None:
    if not isinstance(data, dict) or not isinstance(data.get("scores"), dict):
        raise ValueError("review.scores must be an object")
    if set(data["scores"]) != set(DIMENSIONS):
        raise ValueError("scores must contain exactly: " + ", ".join(DIMENSIONS))
    for key, item in data["scores"].items():
        if not isinstance(item, dict):
            raise ValueError(f"{key} must be an object")
        score = item.get("score")
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 10:
            raise ValueError(f"{key}.score must be finite and between 0 and 10")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence or any(
            not isinstance(value, str) or not value.strip() for value in evidence
        ):
            raise ValueError(f"{key}.evidence must contain nonempty references")
    weights = data.get("weights", {})
    if not isinstance(weights, dict) or set(weights) - set(DIMENSIONS):
        raise ValueError("weights must use known dimensions")
    for key, weight in weights.items():
        if type(weight) not in (int, float) or not math.isfinite(weight) or weight <= 0:
            raise ValueError(f"{key}.weight must be finite and positive")
    if not isinstance(data.get("issues"), list):
        raise ValueError("issues must be an explicit list (empty if none)")
    for issue in data["issues"]:
        if not isinstance(issue, dict) or issue.get("severity") not in {"high", "medium", "low"}:
            raise ValueError("issue.severity must be high, medium or low")
        if not isinstance(issue.get("detail"), str) or not issue["detail"].strip():
            raise ValueError("issue.detail must be nonempty")


def evaluate(data: dict) -> dict:
    validate_review(data)
    summary = summarize_scores(data["scores"], data.get("weights"))
    blockers = [issue for issue in data["issues"] if issue["severity"] == "high"]
    # Numeric suggestions never approve a workflow stage or authenticate evidence.
    suggestion = "blocked" if blockers else (
        "review_ready" if summary["raw_min"] >= 7 and summary["weighted_mean"] >= 8 else "revise"
    )
    return {**summary, "suggestion": suggestion, "issues": data["issues"],
            "stage_approval": False, "evidence_authenticity": "NOT_VERIFIED_BY_SCRIPT"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", help="UTF-8 JSON review; see templates/review-rubric.json")
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.review).read_text(encoding="utf-8-sig"))
        result = evaluate(data)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
    return 3 if result["suggestion"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
