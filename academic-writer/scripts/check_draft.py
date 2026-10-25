"""Gate an academic draft: required sections, placeholders, acronyms, register.

Usage:
    python check_draft.py --dir ./draft --language vi   # or en
    python check_draft.py --file paper.md --language en

Hard failures (exit 1): missing required sections, placeholder text (TODO,
[CHECK], TBD, FIXME, XXX, lorem, "placeholder"), no citations at all.
Warnings: undefined acronyms, contractions (en), missing diacritics (vi),
claims with numbers that lack a nearby table/figure reference.

The checks are heuristics to catch the obvious; human judgment still decides.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED = {
    "en": {
        "abstract": ["abstract"],
        "introduction": ["introduction"],
        "related work": ["related work", "related works"],
        "method": ["method", "methods", "methodology", "approach"],
        "experiments": ["experiment", "experiments", "evaluation", "results"],
        "conclusion": ["conclusion", "conclusions", "discussion"],
    },
    "vi": {
        "abstract": ["tóm tắt", "tóm tắt luận văn"],
        "introduction": ["giới thiệu", "mở đầu", "đặt vấn đề"],
        "related work": ["công trình liên quan", "nghiên cứu liên quan", "các công trình liên quan"],
        "method": ["phương pháp", "phương pháp đề xuất", "cách tiếp cận"],
        "experiments": ["thực nghiệm", "thí nghiệm", "kết quả", "đánh giá"],
        "conclusion": ["kết luận", "kết luận và hướng phát triển"],
    },
}

PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|XXX|XXXL|placeholder|lorem)\b|\[CHECK\]|\[CẦN KIỂM TRA\]", re.IGNORECASE)
CONTRACTION = re.compile(r"\b\w+(n't|'re|'ve|'ll|'d|'m|'s)\b", re.IGNORECASE)
ACRONYM_DEF = re.compile(r"\(([A-Z]{2,8}s?)\)")
ACRONYM_USE = re.compile(r"\b[A-Z]{2,8}\b")
CLAIM_VERBS = re.compile(
    r"\b(achiev|outperform|improv|beat|surpass|reach|attain|boost|reduce|increase|decrease|"
    r"chứng minh|cải thiện|vượt|đạt|tăng|giảm|cho thấy|cho kết quả)\w*\b", re.IGNORECASE)
NUMBER = re.compile(r"\d")
EVIDENCE = re.compile(r"\b(table|figure|fig\.?|bảng|hình)\s*\d", re.IGNORECASE)
DIACRITIC = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", re.IGNORECASE)


def collect_text(paths):
    text, headings = [], []
    for p in paths:
        if not p.exists():
            continue
        if p.suffix != ".md":
            continue
        content = p.read_text(encoding="utf-8")
        text.append(content)
        for line in content.splitlines():
            if line.startswith("#"):
                headings.append(line.lstrip("#").strip().lower())
    return "\n".join(text), headings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--language", choices=["en", "vi"], required=True)
    args = ap.parse_args()

    if args.dir:
        paths = sorted(Path(args.dir).glob("**/*.md"))
    elif args.file:
        paths = [Path(args.file)]
    else:
        raise SystemExit("provide --dir or --file")

    text, headings = collect_text(paths)
    if not text:
        raise SystemExit("no markdown found")

    hard, warn = [], []

    # Required sections
    for label, keys in REQUIRED[args.language].items():
        if not any(k in h for h in headings for k in keys):
            hard.append(f"missing required section: {label}")

    # Placeholders
    for m in PLACEHOLDER.finditer(text):
        hard.append(f"placeholder text: '{m.group(0)}'")

    # Acronyms used but never defined
    defined = set()
    for m in ACRONYM_DEF.finditer(text):
        defined.add(m.group(1).rstrip("s").rstrip("S"))
    used = set(ACRONYM_USE.findall(text))
    for a in sorted(used - defined):
        warn.append(f"acronym '{a}' used but never defined")

    # Register
    if args.language == "en":
        for m in CONTRACTION.finditer(text):
            warn.append(f"contraction in formal English: '{m.group(0)}'")
    else:
        if not DIACRITIC.search(text):
            warn.append("no Vietnamese diacritics detected (check tone marks)")

    # Claims with numbers lacking nearby evidence
    for para in re.split(r"\n\s*\n", text):
        if CLAIM_VERBS.search(para) and NUMBER.search(para) and not EVIDENCE.search(para):
            warn.append("claim with a number but no table/figure reference nearby: "
                        + para.strip()[:80] + "...")

    # No citations
    if not re.search(r"\[\d+\]|\(\w+ et al\.?,? \d{4}\)|\(\d{4}\)", text):
        warn.append("no citations detected in the draft")

    for h in hard:
        print(f"[FAIL] {h}")
    for w in warn:
        print(f"[WARN] {w}")
    print(f"\n{len(hard)} hard failures, {len(warn)} warnings")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
