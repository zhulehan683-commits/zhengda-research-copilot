#!/usr/bin/env python3
"""Dependency-free descriptive and basic inferential statistics.

The module intentionally stops at methods a standard-library implementation can
explain and test. It does not provide SEM, multilevel models, machine learning,
survey weights, or causal identification.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

from common import enable_utf8, fail, within


def _clean(values):
    return [v for v in values if v is not None and math.isfinite(v)]


def mean(values):
    data = _clean(values)
    if not data:
        raise ValueError("mean needs at least one finite value")
    return sum(data) / len(data)


def median(values):
    data = sorted(_clean(values))
    if not data:
        raise ValueError("median needs at least one finite value")
    middle = len(data) // 2
    return data[middle] if len(data) % 2 else (data[middle - 1] + data[middle]) / 2


def variance(values):
    data = _clean(values)
    if len(data) < 2:
        raise ValueError("sample variance needs at least two values")
    centre = sum(data) / len(data)
    return sum((value - centre) ** 2 for value in data) / (len(data) - 1)


def stdev(values):
    return math.sqrt(variance(values))


def quantile(values, probability):
    if not 0 <= probability <= 1:
        raise ValueError("quantile probability must be between 0 and 1")
    data = sorted(_clean(values))
    if not data:
        raise ValueError("quantile needs at least one finite value")
    position = (len(data) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return data[lower]
    return data[lower] + (data[upper] - data[lower]) * (position - lower)


def frequency(values):
    counts = Counter(values)
    total = sum(counts.values())
    return {"n": total, "counts": dict(sorted(counts.items(), key=lambda kv: str(kv[0]))),
            "proportions": {key: count / total for key, count in counts.items()} if total else {}}


def _betacf(a, b, x):
    """Continued fraction for the regularized incomplete beta (Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta I_x(a,b)."""
    if a <= 0 or b <= 0:
        raise ValueError("beta parameters must be positive")
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(value, df):
    if df <= 0:
        raise ValueError("t degrees of freedom must be positive")
    if value == 0:
        return 0.5
    tail = 0.5 * betainc(df / 2.0, 0.5, df / (df + value * value))
    return 1.0 - tail if value > 0 else tail


def t_survival(value, df):
    return 1.0 - t_cdf(value, df)


def t_critical(df, confidence=0.95):
    if df <= 0:
        raise ValueError("t degrees of freedom must be positive")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    target = 1.0 - (1.0 - confidence) / 2.0
    low, high = 0.0, 1.0
    while t_cdf(high, df) < target:
        high *= 2
        if high > 1e6:
            raise ValueError("could not bracket t critical value")
    for _ in range(200):
        mid = (low + high) / 2.0
        if t_cdf(mid, df) < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def _mean_ci(values, confidence):
    data = _clean(values)
    n = len(data)
    if n < 2:
        raise ValueError("confidence interval needs at least two values")
    centre = sum(data) / n
    se = stdev(data) / math.sqrt(n)
    critical = t_critical(n - 1, confidence)
    return {"n": n, "mean": centre, "sd": stdev(data), "se": se,
            "confidence": confidence, "ci_low": centre - critical * se,
            "ci_high": centre + critical * se, "df": n - 1}


def t_test_one(sample, popmean=0.0, confidence=0.95):
    data = _clean(sample)
    n = len(data)
    if n < 2:
        raise ValueError("one-sample t test needs at least two values")
    centre = sum(data) / n
    sd = stdev(data)
    se = sd / math.sqrt(n)
    difference = centre - popmean
    statistic = (difference / se if se else
                 (0.0 if difference == 0 else math.copysign(float("inf"), difference)))
    p_value = 2 * t_survival(abs(statistic), n - 1) if math.isfinite(statistic) else 0.0
    critical = t_critical(n - 1, confidence)
    return {"test": "one-sample t", "n": n, "mean": centre, "sd": sd,
            "popmean": popmean, "t": statistic, "df": n - 1, "p_value": min(1.0, p_value),
            "cohen_d": (centre - popmean) / sd if sd else None,
            "ci_low": centre - critical * se, "ci_high": centre + critical * se}


def t_test_two(first, second, equal_var=False, confidence=0.95):
    a, b = _clean(first), _clean(second)
    if len(a) < 2 or len(b) < 2:
        raise ValueError("two-sample t test needs at least two values per group")
    mean_a, mean_b = sum(a) / len(a), sum(b) / len(b)
    var_a, var_b = variance(a), variance(b)
    diff = mean_a - mean_b
    if equal_var:
        df = len(a) + len(b) - 2
        pooled = ((len(a) - 1) * var_a + (len(b) - 1) * var_b) / df
        se = math.sqrt(pooled * (1 / len(a) + 1 / len(b)))
        method = "Student t (equal variance)"
    else:
        se = math.sqrt(var_a / len(a) + var_b / len(b))
        denominator = (var_a / len(a)) ** 2 / (len(a) - 1) + \
                      (var_b / len(b)) ** 2 / (len(b) - 1)
        df = (var_a / len(a) + var_b / len(b)) ** 2 / denominator if denominator else len(a) + len(b) - 2
        method = "Welch t (unequal variance)"
    statistic = (diff / se if se else
                 (0.0 if diff == 0 else math.copysign(float("inf"), diff)))
    p_value = 2 * t_survival(abs(statistic), df) if math.isfinite(statistic) else 0.0
    critical = t_critical(df, confidence)
    pooled_sd = math.sqrt(((len(a) - 1) * var_a + (len(b) - 1) * var_b)
                          / (len(a) + len(b) - 2))
    return {"test": method, "n1": len(a), "n2": len(b), "mean1": mean_a,
            "mean2": mean_b, "difference": diff, "se": se, "df": df,
            "t": statistic, "p_value": min(1.0, p_value),
            "cohen_d": diff / pooled_sd if pooled_sd else None,
            "ci_low": diff - critical * se, "ci_high": diff + critical * se}


def t_test_paired(first, second, confidence=0.95):
    if len(first) != len(second):
        raise ValueError("paired samples must have equal length")
    differences = [float(a) - float(b) for a, b in zip(first, second)]
    result = t_test_one(differences, 0.0, confidence)
    result["test"] = "paired t"
    result["n_pairs"] = len(differences)
    return result


def _gammainc_series(a, x):
    term = 1.0 / a
    total = term
    for n in range(1, 500):
        term *= x / (a + n)
        total += term
        if abs(term) < abs(total) * 1e-14:
            break
    return total * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gammainc_fraction(a, x):
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b if b else 1.0 / tiny
    h = d
    for index in range(1, 500):
        an = -index * (index - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def gammainc_upper(a, x):
    """Regularized upper incomplete gamma Q(a,x)."""
    if a <= 0 or x < 0:
        raise ValueError("gamma parameters out of range")
    if x == 0:
        return 1.0
    if x < a + 1:
        return 1.0 - _gammainc_series(a, x)
    return _gammainc_fraction(a, x)


def chi_square(table):
    if len(table) < 2 or any(len(row) < 2 for row in table):
        raise ValueError("chi-square needs a table of at least 2x2")
    if any(len(row) != len(table[0]) for row in table):
        raise ValueError("chi-square table rows must have equal length")
    if any(value < 0 for row in table for value in row):
        raise ValueError("chi-square counts cannot be negative")
    rows = [sum(row) for row in table]
    columns = [sum(table[i][j] for i in range(len(table))) for j in range(len(table[0]))]
    total = sum(rows)
    if total == 0:
        raise ValueError("chi-square table is empty")
    expected = [[rows[i] * columns[j] / total for j in range(len(columns))]
                for i in range(len(rows))]
    statistic = sum((table[i][j] - expected[i][j]) ** 2 / expected[i][j]
                    for i in range(len(rows)) for j in range(len(columns))
                    if expected[i][j])
    df = (len(rows) - 1) * (len(columns) - 1)
    p_value = gammainc_upper(df / 2.0, statistic / 2.0)
    small = sum(1 for row in expected for value in row if value < 5)
    return {"test": "chi-square independence", "statistic": statistic, "df": df,
            "p_value": p_value, "n": total, "expected": expected,
            "cells_expected_below_5": small,
            "warning": "expected counts below 5 in some cells; interpret cautiously" if small else None}


def fisher_exact(table):
    if len(table) != 2 or any(len(row) != 2 for row in table):
        raise ValueError("Fisher exact needs a 2x2 table")
    if any(value < 0 or not isinstance(value, int) for row in table for value in row):
        raise ValueError("Fisher exact needs nonnegative integer counts")
    a, b = table[0]
    c, d = table[1]
    n = a + b + c + d
    row1, row2 = a + b, c + d
    col1 = a + c
    denominator = math.comb(n, col1)

    def probability(x):
        return math.comb(row1, x) * math.comb(row2, col1 - x) / denominator

    observed = probability(a)
    lower = max(0, col1 - row2)
    upper = min(row1, col1)
    p_value = sum(probability(x) for x in range(lower, upper + 1)
                  if probability(x) <= observed + 1e-12)
    return {"test": "Fisher exact (two-sided)", "table": table, "n": n,
            "p_value": min(1.0, p_value), "observed_probability": observed}


def cronbach_alpha(rows):
    if not rows or len(rows[0]) < 2:
        raise ValueError("Cronbach alpha needs at least two items")
    if any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("Cronbach alpha rows must have equal length")
    k = len(rows[0])
    item_variances = [variance([row[j] for row in rows]) for j in range(k)]
    totals = [sum(row) for row in rows]
    total_variance = variance(totals)
    if total_variance == 0:
        raise ValueError("Cronbach alpha undefined: total variance is zero")
    alpha = k / (k - 1) * (1 - sum(item_variances) / total_variance)
    return {"test": "Cronbach alpha", "items": k, "n": len(rows),
            "alpha": alpha, "item_variances": item_variances,
            "total_variance": total_variance}


def _invert(matrix):
    size = len(matrix)
    augmented = [list(map(float, row)) + [1.0 if i == j else 0.0 for j in range(size)]
                 for i, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda r: abs(augmented[r][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("matrix is singular; remove collinear predictors or add rows")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor:
                augmented[row] = [value - factor * base for value, base
                                  in zip(augmented[row], augmented[column])]
    return [row[size:] for row in augmented]


def _normal_p(two_sided_z):
    return math.erfc(abs(two_sided_z) / math.sqrt(2.0))


def _design_matrix(rows, names):
    if not names or not rows:
        raise ValueError("at least one predictor is required")
    return [[1.0] + [float(rows[name][i]) for name in names]
            for i in range(len(next(iter(rows.values()))))]


def _complete_rows(y, xs):
    columns = {"y": y, **xs}
    length = len(y)
    if any(len(values) != length for values in columns.values()):
        raise ValueError("all columns must have equal length")
    usable = [i for i in range(length)
              if all(value is not None and math.isfinite(float(value))
                     for value in (column[i] for column in columns.values()))]
    if len(usable) <= len(xs) + 1:
        raise ValueError("not enough complete rows for the number of predictors")
    trimmed = {name: [float(values[i]) for i in usable] for name, values in columns.items()}
    return trimmed["y"], {name: trimmed[name] for name in xs}, len(usable), length


def ols(y, xs, feature_names=None):
    y, xs, used, total = _complete_rows(y, xs)
    names = feature_names or list(xs)
    matrix = _design_matrix(xs, names)
    n, p = len(matrix), len(matrix[0])
    xtx = [[sum(matrix[i][a] * matrix[i][b] for i in range(n)) for b in range(p)]
           for a in range(p)]
    xty = [sum(matrix[i][a] * y[i] for i in range(n)) for a in range(p)]
    inverse = _invert(xtx)
    beta = [sum(inverse[a][b] * xty[b] for b in range(p)) for a in range(p)]
    fitted = [sum(matrix[i][a] * beta[a] for a in range(p)) for i in range(n)]
    residuals = [y[i] - fitted[i] for i in range(n)]
    sse = sum(value * value for value in residuals)
    mean_y = sum(y) / n
    sst = sum((value - mean_y) ** 2 for value in y)
    df = n - p
    mse = sse / df if df > 0 else None
    covariance = [[inverse[a][b] * mse for b in range(p)] for a in range(p)] if mse else None
    se = [math.sqrt(max(0.0, covariance[a][a])) for a in range(p)] if covariance else [None] * p
    statistics = [beta[a] / se[a] if se[a] else None for a in range(p)]
    p_values = [2 * t_survival(abs(value), df) if value is not None else None
                for value in statistics]
    r_squared = 1 - sse / sst if sst else None
    adjusted = (1 - (1 - r_squared) * (n - 1) / df
                if r_squared is not None and df > 0 else None)
    return {"test": "OLS", "n": n, "n_dropped": total - used,
            "predictors": names, "coefficients": dict(zip(["intercept"] + names, beta)),
            "std_errors": dict(zip(["intercept"] + names, se)),
            "t_values": dict(zip(["intercept"] + names, statistics)),
            "p_values": dict(zip(["intercept"] + names, p_values)),
            "r_squared": r_squared,
            "adjusted_r_squared": adjusted,
            "residual_sd": math.sqrt(mse) if mse is not None else None,
            "df_residual": df, "sse": sse, "sst": sst}


def logit(y, xs, feature_names=None):
    y, xs, used, total = _complete_rows(y, xs)
    if any(value not in (0.0, 1.0) for value in y):
        raise ValueError("logit outcome must be coded 0/1")
    names = feature_names or list(xs)
    matrix = _design_matrix(xs, names)
    n, p = len(matrix), len(matrix[0])
    beta = [0.0] * p
    converged = False
    for iteration in range(100):
        eta = [sum(matrix[i][a] * beta[a] for a in range(p)) for i in range(n)]
        mu = [1.0 / (1.0 + math.exp(-max(-700.0, min(700.0, value)))) for value in eta]
        weights = [max(value * (1 - value), 1e-12) for value in mu]
        z = [eta[i] + (y[i] - mu[i]) / weights[i] for i in range(n)]
        xtwx = [[sum(matrix[i][a] * weights[i] * matrix[i][b] for i in range(n))
                 for b in range(p)] for a in range(p)]
        xtwz = [sum(matrix[i][a] * weights[i] * z[i] for i in range(n)) for a in range(p)]
        inverse = _invert(xtwx)
        updated = [sum(inverse[a][b] * xtwz[b] for b in range(p)) for a in range(p)]
        if max(abs(updated[a] - beta[a]) for a in range(p)) < 1e-9:
            beta = updated
            converged = True
            break
        beta = updated
    if not converged:
        raise ValueError("logit did not converge; inspect separation or scaling")
    eta = [sum(matrix[i][a] * beta[a] for a in range(p)) for i in range(n)]
    mu = [1.0 / (1.0 + math.exp(-max(-700.0, min(700.0, value)))) for value in eta]
    weights = [max(value * (1 - value), 1e-12) for value in mu]
    xtwx = [[sum(matrix[i][a] * weights[i] * matrix[i][b] for i in range(n))
             for b in range(p)] for a in range(p)]
    covariance = _invert(xtwx)
    se = [math.sqrt(max(0.0, covariance[a][a])) for a in range(p)]
    statistics = [beta[a] / se[a] if se[a] else None for a in range(p)]
    p_values = [_normal_p(value) if value is not None else None for value in statistics]
    log_likelihood = sum(y[i] * math.log(max(mu[i], 1e-15))
                         + (1 - y[i]) * math.log(max(1 - mu[i], 1e-15)) for i in range(n))
    base = sum(y) / n
    null_ll = sum(y[i] * math.log(max(base, 1e-15))
                  + (1 - y[i]) * math.log(max(1 - base, 1e-15)) for i in range(n))
    separation = any(value < 1e-6 or value > 1 - 1e-6 for value in mu)
    return {"test": "binary logit (IRLS)", "n": n, "n_dropped": total - used,
            "predictors": names,
            "coefficients": dict(zip(["intercept"] + names, beta)),
            "std_errors": dict(zip(["intercept"] + names, se)),
            "z_values": dict(zip(["intercept"] + names, statistics)),
            "p_values": dict(zip(["intercept"] + names, p_values)),
            "odds_ratios": {name: math.exp(value) for name, value in
                            zip(["intercept"] + names, beta)},
            "log_likelihood": log_likelihood, "pseudo_r_squared": 1 - log_likelihood / null_ll
            if null_ll else None, "iterations": iteration + 1,
            "warning": "possible separation or near-perfect prediction" if separation else None}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("CSV needs a header row")
        return list(reader.fieldnames), list(reader)


def numeric_column(rows, name, missing=("", "NA", "N/A", "null", "NULL")):
    if name not in (rows[0] if rows else {}):
        raise ValueError(f"column not found: {name}")
    values = []
    for row in rows:
        raw = (row.get(name) or "").strip()
        if raw in missing:
            values.append(None)
        else:
            values.append(float(raw))
    return values


def main() -> int:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    describe = sub.add_parser("describe")
    describe.add_argument("--data", required=True)
    describe.add_argument("--columns", required=True)
    describe.add_argument("--confidence", type=float, default=0.95)
    ttest = sub.add_parser("ttest")
    ttest.add_argument("--data", required=True)
    ttest.add_argument("--value", required=True)
    ttest.add_argument("--group")
    ttest.add_argument("--popmean", type=float, default=0.0)
    ttest.add_argument("--equal-var", action="store_true")
    chisq = sub.add_parser("chisq")
    chisq.add_argument("--data", required=True)
    chisq.add_argument("--row", required=True)
    chisq.add_argument("--col", required=True)
    fisher = sub.add_parser("fisher")
    fisher.add_argument("--data", required=True)
    fisher.add_argument("--row", required=True)
    fisher.add_argument("--col", required=True)
    alpha = sub.add_parser("alpha")
    alpha.add_argument("--data", required=True)
    alpha.add_argument("--columns", required=True)
    regression = sub.add_parser("ols")
    regression.add_argument("--data", required=True)
    regression.add_argument("--y", required=True)
    regression.add_argument("--x", required=True)
    logit_parser = sub.add_parser("logit")
    logit_parser.add_argument("--data", required=True)
    logit_parser.add_argument("--y", required=True)
    logit_parser.add_argument("--x", required=True)
    args = parser.parse_args()
    try:
        if args.command in {"chisq", "fisher"}:
            _, rows = read_csv(Path(args.data))
            table = [[0] * len(sorted({r[args.col] for r in rows}))
                     for _ in sorted({r[args.row] for r in rows})]
            row_index = {value: i for i, value in enumerate(sorted({r[args.row] for r in rows}))}
            col_index = {value: j for j, value in enumerate(sorted({r[args.col] for r in rows}))}
            for row in rows:
                table[row_index[row[args.row]]][col_index[row[args.col]]] += 1
            result = chi_square(table) if args.command == "chisq" else fisher_exact(table)
        else:
            _, rows = read_csv(Path(args.data))
            if not rows:
                raise ValueError("CSV has no data rows")
            if args.command == "describe":
                result = {}
                for name in [n.strip() for n in args.columns.split(",") if n.strip()]:
                    values = numeric_column(rows, name)
                    result[name] = {"n": len(_clean(values)),
                                    **_mean_ci(values, args.confidence),
                                    "min": min(_clean(values)),
                                    "max": max(_clean(values)),
                                    "median": median(values)}
            elif args.command == "ttest":
                values = numeric_column(rows, args.value)
                if args.group:
                    groups = {}
                    for row, value in zip(rows, values):
                        groups.setdefault(row[args.group], []).append(value)
                    keys = sorted(groups)
                    if len(keys) != 2:
                        raise ValueError("ttest --group needs exactly two groups")
                    result = t_test_two(groups[keys[0]], groups[keys[1]],
                                        equal_var=args.equal_var)
                else:
                    result = t_test_one(values, args.popmean)
            elif args.command == "alpha":
                names = [n.strip() for n in args.columns.split(",") if n.strip()]
                matrix = list(zip(*(numeric_column(rows, name) for name in names)))
                complete = [list(row) for row in matrix if all(v is not None for v in row)]
                result = cronbach_alpha(complete)
            else:
                xs = {name.strip(): numeric_column(rows, name.strip())
                      for name in args.x.split(",") if name.strip()}
                y = numeric_column(rows, args.y)
                result = ols(y, xs) if args.command == "ols" else logit(y, xs)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, csv.Error) as exc:
        return fail(exc)


if __name__ == "__main__":
    sys.exit(main())
