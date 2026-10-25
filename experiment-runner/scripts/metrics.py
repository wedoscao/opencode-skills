"""Dependency-free (numpy-only) evaluation metrics for scoring experiments.

Functions:
    auroc(y_true, score)                 -> float          Mann-Whitney AUROC with ties
    bootstrap_auc_ci(y_true, score, ...) -> (lo, hi, boot) percentile bootstrap CI
    delong_test(y_true, s_a, s_b)        -> (auc_a, auc_b, z, p) paired DeLong test
    accuracy(y_true, y_pred)             -> float
    ece(y_true, proba, n_bins=10)        -> float          expected calibration error

CLI:
    python metrics.py --y_true y.json --scores a.json [--scores2 b.json] \
        [--bootstrap 2000] [--ci 0.95] [--seed 0]

`--scores2` triggers a DeLong paired comparison between the two score files.
Input files are JSON arrays (or newline-separated numbers).
"""
from __future__ import annotations

import argparse
import json
import math

import numpy as np


def _tie_averaged_ranks(values: np.ndarray) -> np.ndarray:
    """Ranks of `values` with ties averaged (1-based)."""
    order = np.argsort(values, kind="mergesort")
    vs = values[order]
    r = np.empty(values.size, dtype=float)
    i = 0
    n = values.size
    while i < n:
        j = i
        while j + 1 < n and vs[j + 1] == vs[i]:
            j += 1
        r[order[i : j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return r


def auroc(y_true, score) -> float:
    """Area under the ROC curve via the Mann-Whitney U statistic (handles ties)."""
    y_true = np.asarray(y_true, dtype=np.int64)
    score = np.asarray(score, dtype=float)
    if y_true.size != score.size:
        raise ValueError("y_true and score must be the same length")
    n_pos = int((y_true == 1).sum())
    n_neg = int((y_true == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = _tie_averaged_ranks(score)
    sum_rank_pos = ranks[y_true == 1].sum()
    return float((sum_rank_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def bootstrap_auc_ci(y_true, score, n_boot: int = 2000, ci: float = 0.95, seed: int = 0):
    """Percentile bootstrap confidence interval for AUROC."""
    y_true = np.asarray(y_true, dtype=np.int64)
    score = np.asarray(score, dtype=float)
    rng = np.random.default_rng(seed)
    n = y_true.size
    vals = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        vals[b] = auroc(y_true[idx], score[idx])
    alpha = 1.0 - ci
    lo = float(np.percentile(vals, 100 * alpha / 2))
    hi = float(np.percentile(vals, 100 * (1 - alpha / 2)))
    return lo, hi, vals


def _v10_v01(y_true, score):
    """DeLong structural components: per-positive V10 and per-negative V01."""
    y_true = np.asarray(y_true, dtype=np.int64)
    score = np.asarray(score, dtype=float)
    pos = score[y_true == 1]
    neg = score[y_true == 0]
    n_pos = pos.size
    n_neg = neg.size
    neg_sorted = np.sort(neg)
    pos_sorted = np.sort(pos)
    v10 = np.empty(n_pos)
    v01 = np.empty(n_neg)
    for k, s in enumerate(pos):
        less = np.searchsorted(neg_sorted, s, side="left")
        eq = np.searchsorted(neg_sorted, s, side="right") - less
        v10[k] = (less + 0.5 * eq) / n_neg
    for l, s in enumerate(neg):
        right = np.searchsorted(pos_sorted, s, side="right")
        left = np.searchsorted(pos_sorted, s, side="left")
        greater = n_pos - right
        eq = right - left
        v01[l] = (greater + 0.5 * eq) / n_pos
    return v10, v01


def _auc_and_var(y_true, score):
    v10, v01 = _v10_v01(y_true, score)
    auc = float(v10.mean())
    n_pos = v10.size
    n_neg = v01.size
    s10 = float(np.sum((v10 - auc) ** 2) / (n_pos - 1))
    s01 = float(np.sum((v01 - auc) ** 2) / (n_neg - 1))
    var = s10 / n_pos + s01 / n_neg
    return auc, var, v10, v01


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def delong_test(y_true, score_a, score_b):
    """DeLong's paired test that the AUROC of two score vectors on the SAME
    samples differ. Returns (auc_a, auc_b, z, two-sided p)."""
    y_true = np.asarray(y_true, dtype=np.int64)
    score_a = np.asarray(score_a, dtype=float)
    score_b = np.asarray(score_b, dtype=float)
    if not (y_true.size == score_a.size == score_b.size):
        raise ValueError("y_true, score_a, score_b must be the same length")
    auc_a, var_a, v10a, v01a = _auc_and_var(y_true, score_a)
    auc_b, var_b, v10b, v01b = _auc_and_var(y_true, score_b)
    n_pos = v10a.size
    n_neg = v01a.size
    s10 = float(np.sum((v10a - auc_a) * (v10b - auc_b)) / (n_pos - 1))
    s01 = float(np.sum((v01a - auc_a) * (v01b - auc_b)) / (n_neg - 1))
    cov = s10 / n_pos + s01 / n_neg
    var_diff = var_a + var_b - 2.0 * cov
    if abs(auc_a - auc_b) < 1e-12:
        return auc_a, auc_b, 0.0, 1.0
    if var_diff <= 0:
        return auc_a, auc_b, float("nan"), float("nan")
    z = (auc_a - auc_b) / math.sqrt(var_diff)
    p = 2.0 * (1.0 - _norm_cdf(abs(z)))
    return auc_a, auc_b, z, p


def accuracy(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if y_true.size != y_pred.size:
        raise ValueError("length mismatch")
    return float((y_true == y_pred).mean())


def ece(y_true, proba, n_bins: int = 10) -> float:
    """Expected calibration error (confidence vs accuracy in bins)."""
    y_true = np.asarray(y_true, dtype=int)
    proba = np.asarray(proba, dtype=float)
    if y_true.size != proba.size:
        raise ValueError("length mismatch")
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    total = y_true.size
    err = 0.0
    for b in range(n_bins):
        mask = (proba > bins[b]) & (proba <= bins[b + 1])
        cnt = int(mask.sum())
        if cnt == 0:
            continue
        conf = float(proba[mask].mean())
        acc = float(y_true[mask].mean())
        err += (cnt / total) * abs(conf - acc)
    return err


def _load(path: str) -> np.ndarray:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read().strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = [float(x) for x in text.split()]
    return np.asarray(data, dtype=float)


def _main() -> None:
    ap = argparse.ArgumentParser(description="Scoring-experiment metrics")
    ap.add_argument("--y_true", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--scores2", default=None, help="second score file -> DeLong test")
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--ci", type=float, default=0.95)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    y = _load(args.y_true).astype(np.int64)
    s = _load(args.scores)

    out = {"auroc": auroc(y, s)}
    lo, hi, _ = bootstrap_auc_ci(y, s, n_boot=args.bootstrap, ci=args.ci, seed=args.seed)
    out[f"auc_ci_{int(100*args.ci)}"] = [round(lo, 4), round(hi, 4)]
    if args.scores2:
        s2 = _load(args.scores2)
        auc_a, auc_b, z, p = delong_test(y, s, s2)
        out["delong"] = {"auc_a": round(auc_a, 4), "auc_b": round(auc_b, 4),
                         "z": round(z, 4), "p": round(p, 4)}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    _main()
