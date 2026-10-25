#!/usr/bin/env python3
"""Gate a filled roadmap against the skill's own definition of done.

scaffold.py can only guarantee structure; this checks whether the *filled* plan actually
answers the hard questions: no leftover TODOs, a research question (not a template), a
falsification criterion, enough baselines/datasets/seeds for the chosen target, venue
rows filled, risks with fallbacks, and gates present. It is the cheap "is this a plan or
a wish?" test before the agent hands anything to the user.

CLI:
  python check_plan.py --dir ./roadmap [--target journal-q1q2] [--library ~/Papers]
"""
import argparse
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = json.load(open(os.path.join(HERE, "..", "references", "targets.json"), encoding="utf-8"))

FILES = ["PROPOSAL.md", "GAP-TABLE.csv", "EXPERIMENTS.md", "TARGET.md",
         "ROADMAP.md", "RISKS.md", "OUTLINE.md"]

FALSIFY_HINTS = re.compile(r"falsif|bác bỏ|bị bác|không đạt thì|nếu.*không|giả thuyết.*sai", re.I)


def _min(req):
    """Turn '1–2' / '3–5' / 3 into the minimum int."""
    m = re.match(r"\s*(\d+)", str(req))
    return int(m.group(1)) if m else 0


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def table_rows(md, header_cell):
    """Return data rows (non-header, non-separator) of the first table whose header
    contains header_cell. Rows are lists of stripped cells."""
    rows = []
    for block in re.split(r"\n\s*\n", md):
        lines = block.splitlines()
        for i, ln in enumerate(lines):
            if ln.strip().startswith("|") and header_cell in ln and not re.match(r"^\s*\|[\s:\-|]+\|", ln):
                # header found; data rows follow until a non-table line
                for data in lines[i + 1:]:
                    if not data.strip().startswith("|"):
                        break
                    if re.match(r"^\s*\|[\s:\-|]+\|\s*$", data):
                        continue
                    cells = [c.strip() for c in data.strip().strip("|").split("|")]
                    if any(cells) and all("TODO" not in c for c in cells):
                        rows.append(cells)
                return rows
    return rows


def count_filled_todos(path):
    text = read(path)
    return text.count("TODO")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True, help="Roadmap directory produced by scaffold.py")
    ap.add_argument("--target", help="Override target key (default: read from TARGET.md)")
    ap.add_argument("--library", help="Optional paper library root, to count coverage per direction")
    args = ap.parse_args()

    errors, warns = [], []

    missing = [f for f in FILES if not os.path.exists(os.path.join(args.dir, f))]
    if missing:
        errors.append(f"missing files: {', '.join(missing)}")

    for f in FILES:
        p = os.path.join(args.dir, f)
        if not os.path.exists(p):
            continue
        n = count_filled_todos(p)
        if n:
            if f == "GAP-TABLE.csv":
                warns.append(f"{f}: still has {n} 'TODO' (gap table should be fully filled first)")
            else:
                errors.append(f"{f}: {n} unresolved 'TODO'")

    proposal = os.path.join(args.dir, "PROPOSAL.md")
    if os.path.exists(proposal):
        text = read(proposal)
        if "RQ1: TODO" in text:
            errors.append("PROPOSAL.md: RQ1 is still a TODO")
        if not FALSIFY_HINTS.search(text):
            warns.append("PROPOSAL.md: no falsification criterion found (how would this RQ be shown wrong?)")

    target_md = os.path.join(args.dir, "TARGET.md")
    target_text = read(target_md) if os.path.exists(target_md) else ""
    tkey = args.target
    if not tkey:
        m = re.search(r"`(thesis|conf-domestic|conf-intl|journal-q1q2|journal-q3q4|grant)`", target_text)
        tkey = m.group(1) if m else None

    experiments = os.path.join(args.dir, "EXPERIMENTS.md")
    if os.path.exists(experiments):
        text = read(experiments)
        if not tkey:
            warns.append("EXPERIMENTS.md: could not determine target profile; requirements not checked")
        else:
            t = TARGETS[tkey]
            n_base = len(table_rows(text, "Baseline"))
            n_data = len(table_rows(text, "Dataset"))
            need_base, need_data, need_seed = _min(t["baselines"]), _min(t["datasets"]), _min(t["seeds"])
            if n_base < need_base:
                errors.append(f"EXPERIMENTS.md: {n_base} baselines listed, target '{tkey}' needs ≥{need_base}")
            if n_data < need_data:
                errors.append(f"EXPERIMENTS.md: {n_data} datasets listed, target '{tkey}' needs ≥{need_data}")
            if f"{need_seed} seed" not in text and f"{need_seed} seed" not in text:
                warns.append(f"EXPERIMENTS.md: confirm {need_seed} seeds are planned (mean ± std)")

    if os.path.exists(target_md):
        n_venue = len(table_rows(target_text, "Venue"))
        if n_venue == 0:
            warns.append("TARGET.md: venue table is empty (run venue_check.py for 3–5 venues)")

    risks = os.path.join(args.dir, "RISKS.md")
    if os.path.exists(risks):
        rows = table_rows(read(risks), "Rủi ro")
        if rows:
            no_fallback = [r[0] for r in rows if len(r) < 5 or not r[-1]]
            if no_fallback:
                warns.append(f"RISKS.md: risks without a fallback plan: {', '.join(no_fallback[:4])}")

    gap = os.path.join(args.dir, "GAP-TABLE.csv")
    if os.path.exists(gap):
        with open(gap, encoding="utf-8") as f:
            rows = [r for r in csv.reader(f) if any(c.strip() for c in r) and not all("TODO" in c for c in r)]
        data = rows[1:]  # drop header
        if len(data) < 6:
            warns.append(f"GAP-TABLE.csv: only {len(data)} filled rows (skill asks ~6+ in the sub-area)")

    if args.library and os.path.isdir(args.library):
        per = {}
        for d in sorted(glob.glob(os.path.join(args.library, "*"))):
            if os.path.isdir(d):
                pdfs = glob.glob(os.path.join(d, "*.pdf"))
                per[os.path.basename(d)] = len(pdfs)
        total = sum(per.values())
        print(f"library: {total} PDFs across {len(per)} folders")
        for d, n in per.items():
            flag = "  <-- thin" if n < 6 else ""
            print(f"  {d}: {n}{flag}")
        if per and min(per.values()) < 6:
            warns.append("some library folders have <6 papers; consider fetching more before trusting the gap table")

    print()
    if warns:
        print(f"{len(warns)} warning(s):")
        for w in warns:
            print("  WARN " + w)
    if errors:
        print(f"{len(errors)} error(s):")
        for e in errors:
            print("  ERROR " + e)
        print("\nPlan is not done — fix the errors above.")
        sys.exit(1)
    print("Plan passes the definition-of-done gate." if not warns else "Plan passes with warnings.")
    sys.exit(0)


if __name__ == "__main__":
    main()
