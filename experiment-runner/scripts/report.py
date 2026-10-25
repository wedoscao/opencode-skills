"""Aggregate per-run result JSONs into a markdown matrix + cost table.

Usage:
    python report.py --results results --out RESULTS.md --metric auroc \
        --methods b1 b2 b3 --datasets probe-vi vihallu

Each result JSON is the schema written by src/run.py:
    {run_id, method, model, dataset, seed, metrics{}, cost{}}
Cells show mean ± std across seeds for the chosen metric. A second table
sums cost (forward passes, wall-clock) per method.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def _mean_std(vals):
    if not vals:
        return "-"
    m = sum(vals) / len(vals)
    if len(vals) == 1:
        return f"{m:.4f}"
    var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
    return f"{m:.4f} ± {var ** 0.5:.4f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="RESULTS.md")
    ap.add_argument("--metric", default="auroc")
    ap.add_argument("--methods", nargs="*", default=None, help="row order")
    ap.add_argument("--datasets", nargs="*", default=None, help="column order")
    args = ap.parse_args()

    runs = []
    for f in sorted(Path(args.results).glob("*.json")):
        runs.append(json.loads(f.read_text()))

    if not runs:
        raise SystemExit(f"no result JSONs found in {args.results}")

    methods = args.methods or sorted({r["method"] for r in runs})
    datasets = args.datasets or sorted({r["dataset"] for r in runs})

    # method -> dataset -> list of metric values
    cells = defaultdict(lambda: defaultdict(list))
    costs = defaultdict(lambda: defaultdict(float))
    for r in runs:
        m, d = r["method"], r["dataset"]
        v = (r.get("metrics") or {}).get(args.metric)
        if v is not None:
            cells[m][d].append(v)
        c = r.get("cost") or {}
        costs[m]["forward_passes"] += c.get("forward_passes") or 0
        costs[m]["wall_clock_s"] += c.get("wall_clock_s") or 0.0

    lines = [f"# Results — {args.metric}", ""]
    lines.append("| method | " + " | ".join(datasets) + " |")
    lines.append("|" + "---|" * (len(datasets) + 1))
    for m in methods:
        row = [f"{_mean_std(cells[m].get(d, []))}" for d in datasets]
        lines.append(f"| {m} | " + " | ".join(row) + " |")

    lines += ["", "## Cost", ""]
    lines.append("| method | forward passes | wall-clock (s) |")
    lines.append("|---|---|---|")
    for m in methods:
        lines.append(f"| {m} | {costs[m]['forward_passes']} | "
                     f"{costs[m]['wall_clock_s']:.1f} |")

    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
