#!/usr/bin/env python3
"""Sample-size and power calculators using only the Python standard library.

These are planning approximations for common undergraduate survey designs. They
do not replace a statistician, account for complex survey designs, or justify a
sample after the fact.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from statistics import NormalDist

from common import enable_utf8, fail


def _z(probability: float) -> float:
    if not 0 < probability < 1:
        raise ValueError("probability must be between 0 and 1")
    return NormalDist().inv_cdf(probability)


def _inflate(n: float, dropout: float) -> int:
    if not 0 <= dropout < 1:
        raise ValueError("dropout must be in [0, 1)")
    return math.ceil(n / (1 - dropout)) if n else 0


def _check_proportion(value: float, name: str) -> None:
    if not 0 < value < 1:
        raise ValueError(f"{name} must be between 0 and 1")


def sample_size_proportion(p=0.5, margin=0.05, confidence=0.95,
                           population=None, dropout=0.0):
    _check_proportion(p, "p")
    if not 0 < margin < 1:
        raise ValueError("margin must be between 0 and 1")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    if population is not None and population <= 1:
        raise ValueError("population must exceed 1 when provided")
    critical = _z(1 - (1 - confidence) / 2)
    n0 = critical ** 2 * p * (1 - p) / margin ** 2
    n = math.ceil(n0)
    if population is not None:
        n = math.ceil(n0 / (1 + (n0 - 1) / population))
    return {"design": "one-proportion precision", "p": p, "margin": margin,
            "confidence": confidence, "finite_population": population,
            "n_before_dropout": n, "dropout": dropout,
            "n": _inflate(n, dropout),
            "assumptions": ["random or approximately random selection",
                            "margin is a half-width, not a full range",
                            "finite-population correction uses the supplied population"]}


def power_two_proportions(p1, p2, n1, n2=None, alpha=0.05):
    _check_proportion(p1, "p1")
    _check_proportion(p2, "p2")
    if n1 <= 1:
        raise ValueError("n1 must exceed 1")
    n2 = n2 or n1
    if n2 <= 1:
        raise ValueError("n2 must exceed 1")
    if p1 == p2:
        return {"power": float("nan"), "note": "p1 equals p2; effect size is zero"}
    critical = _z(1 - alpha / 2)
    pooled = (n1 * p1 + n2 * p2) / (n1 + n2)
    se_null = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    se_alt = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    difference = abs(p1 - p2)
    power = (1 - NormalDist().cdf((critical * se_null - difference) / se_alt)
             + NormalDist().cdf((-critical * se_null - difference) / se_alt))
    return {"design": "two-proportion test", "p1": p1, "p2": p2, "n1": n1,
            "n2": n2, "alpha": alpha, "power": min(1.0, max(0.0, power)),
            "approximation": "normal approximation; no continuity correction"}


def sample_size_two_proportions(p1, p2, power=0.8, alpha=0.05, ratio=1.0,
                                dropout=0.0):
    _check_proportion(p1, "p1")
    _check_proportion(p2, "p2")
    if p1 == p2:
        raise ValueError("p1 and p2 must differ")
    if not 0 < power < 1 or not 0 < alpha < 1:
        raise ValueError("power and alpha must be between 0 and 1")
    if ratio <= 0:
        raise ValueError("ratio must be positive")
    low, high = 2, 1_000_000
    while low < high:
        mid = (low + high) // 2
        current = power_two_proportions(p1, p2, mid, max(2, round(mid * ratio)), alpha)
        if current["power"] >= power:
            high = mid
        else:
            low = mid + 1
    n1 = low
    n2 = max(2, round(n1 * ratio))
    achieved = power_two_proportions(p1, p2, n1, n2, alpha)
    result = {"design": "two-proportion power", "p1": p1, "p2": p2,
            "alpha": alpha, "target_power": power, "n1": _inflate(n1, dropout),
            "n2": _inflate(n2, dropout), "n_total": _inflate(n1, dropout) + _inflate(n2, dropout),
            "achieved_power_before_dropout": achieved["power"],
            "dropout": dropout,
            "assumptions": ["independent groups", "normal approximation",
                            "no continuity correction"]}
    if achieved["power"] < power:
        result["warning"] = "target not reached within search limit; use a specialized tool"
    return result


def power_means(delta, sd, n1, n2=None, alpha=0.05):
    if delta <= 0 or sd <= 0:
        raise ValueError("delta and sd must be positive")
    if n1 <= 1:
        raise ValueError("n1 must exceed 1")
    n2 = n2 or n1
    if n2 <= 1:
        raise ValueError("n2 must exceed 1")
    critical = _z(1 - alpha / 2)
    se = sd * math.sqrt(1 / n1 + 1 / n2)
    z_power = delta / se - critical
    return {"design": "two-mean test", "delta": delta, "sd": sd,
            "n1": n1, "n2": n2, "alpha": alpha,
            "power": min(1.0, max(0.0, NormalDist().cdf(z_power))),
            "approximation": "normal approximation; use a pilot SD"}


def sample_size_means(delta, sd, power=0.8, alpha=0.05, ratio=1.0, dropout=0.0):
    if delta <= 0 or sd <= 0:
        raise ValueError("delta and sd must be positive")
    if not 0 < power < 1 or not 0 < alpha < 1:
        raise ValueError("power and alpha must be between 0 and 1")
    if ratio <= 0:
        raise ValueError("ratio must be positive")
    critical = _z(1 - alpha / 2)
    target = _z(power)
    n1 = math.ceil((critical + target) ** 2 * (1 + 1 / ratio) * sd ** 2 / delta ** 2)
    n2 = max(2, round(n1 * ratio))
    achieved = power_means(delta, sd, max(2, n1), n2, alpha)
    return {"design": "two-mean power", "delta": delta, "sd": sd,
            "alpha": alpha, "target_power": power, "n1": _inflate(max(2, n1), dropout),
            "n2": _inflate(n2, dropout), "n_total": _inflate(max(2, n1), dropout) + _inflate(n2, dropout),
            "achieved_power_before_dropout": achieved["power"],
            "dropout": dropout,
            "assumptions": ["independent groups", "common SD", "normal approximation"]}


def sample_size_chisq(effect_w, df=1, power=0.8, alpha=0.05, dropout=0.0):
    if effect_w <= 0 or df <= 0:
        raise ValueError("effect_w and df must be positive")
    if not 0 < power < 1 or not 0 < alpha < 1:
        raise ValueError("power and alpha must be between 0 and 1")
    critical = _z(1 - alpha / 2)
    target = _z(power)
    n = math.ceil((critical + target) ** 2 / effect_w ** 2)
    return {"design": "chi-square power (approximation)", "effect_size_w": effect_w,
            "df": df, "alpha": alpha, "target_power": power,
            "n_before_dropout": n, "n": _inflate(n, dropout), "dropout": dropout,
            "approximation": ("normal approximation; df is reported but not used in this "
                              "upper-bound estimate. Use a specialized tool for small effects.")}


def main() -> int:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    proportion = sub.add_parser("proportion")
    proportion.add_argument("--p", type=float, default=0.5)
    proportion.add_argument("--margin", type=float, default=0.05)
    proportion.add_argument("--confidence", type=float, default=0.95)
    proportion.add_argument("--population", type=int)
    proportion.add_argument("--dropout", type=float, default=0.0)
    two = sub.add_parser("two-proportions")
    two.add_argument("--p1", type=float, required=True)
    two.add_argument("--p2", type=float, required=True)
    two.add_argument("--power", type=float, default=0.8)
    two.add_argument("--alpha", type=float, default=0.05)
    two.add_argument("--ratio", type=float, default=1.0)
    two.add_argument("--dropout", type=float, default=0.0)
    means = sub.add_parser("mean")
    means.add_argument("--delta", type=float, required=True)
    means.add_argument("--sd", type=float, required=True)
    means.add_argument("--power", type=float, default=0.8)
    means.add_argument("--alpha", type=float, default=0.05)
    means.add_argument("--ratio", type=float, default=1.0)
    means.add_argument("--dropout", type=float, default=0.0)
    chisq = sub.add_parser("chisq")
    chisq.add_argument("--effect-size", type=float, required=True)
    chisq.add_argument("--df", type=int, default=1)
    chisq.add_argument("--power", type=float, default=0.8)
    chisq.add_argument("--alpha", type=float, default=0.05)
    chisq.add_argument("--dropout", type=float, default=0.0)
    args = parser.parse_args()
    try:
        if args.command == "proportion":
            result = sample_size_proportion(args.p, args.margin, args.confidence,
                                            args.population, args.dropout)
        elif args.command == "two-proportions":
            result = sample_size_two_proportions(args.p1, args.p2, args.power,
                                                 args.alpha, args.ratio, args.dropout)
        elif args.command == "mean":
            result = sample_size_means(args.delta, args.sd, args.power, args.alpha,
                                       args.ratio, args.dropout)
        else:
            result = sample_size_chisq(args.effect_size, args.df, args.power,
                                       args.alpha, args.dropout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, TypeError) as exc:
        return fail(exc)


if __name__ == "__main__":
    sys.exit(main())
