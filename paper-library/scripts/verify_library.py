#!/usr/bin/env python3
"""Verify that every PDF in the library matches its citation.

Checks per file: %PDF magic, minimum size, page count, and token overlap
between the Crossref title (from the download log) and the text on page 1.
Also reports duplicate files by hash, which usually means one paper was saved
twice under different names.

Exit code is non-zero when problems are found, so it can gate a final report.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

MIN_PAGES = 4
MIN_BYTES = 20_000


def norm(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", text)


def pdfinfo(path):
    if not shutil.which("pdfinfo"):
        return None
    out = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else None


def first_page_text(path):
    if not shutil.which("pdftotext"):
        return ""
    return subprocess.run(["pdftotext", "-f", "1", "-l", "1", path, "-"],
                          capture_output=True, text=True).stdout


def title_match(expected, page_text):
    """Token overlap is more robust than string similarity: PDFs break lines."""
    tokens = [w for w in norm(expected).split() if len(w) > 4][:8]
    if not tokens:
        return True, 0, 0
    body = norm(page_text[:4000])
    hits = sum(1 for w in tokens if w in body)
    return hits >= max(2, int(len(tokens) * 0.4)), hits, len(tokens)


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="Library root")
    ap.add_argument("--log", help="download-log.json (enables title verification)")
    ap.add_argument("--quiet", action="store_true", help="Only print problems")
    args = ap.parse_args()

    titles = {}
    if args.log and os.path.exists(args.log):
        for rec in json.load(open(args.log, encoding="utf-8")):
            if rec.get("file") and (rec.get("meta") or {}).get("title"):
                titles[os.path.normpath(rec["file"])] = rec["meta"]["title"]

    pdfs = []
    for dirpath, _, files in os.walk(args.root):
        for name in files:
            if name.lower().endswith(".pdf"):
                pdfs.append(os.path.join(dirpath, name))
    pdfs.sort()

    problems, hashes = [], {}
    for path in pdfs:
        rel = os.path.normpath(os.path.relpath(path, args.root))
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            magic_ok = f.read(5) == b"%PDF-"
        pages = pdfinfo(path)
        issues = []
        if not magic_ok:
            issues.append("not a PDF")
        if size < MIN_BYTES:
            issues.append(f"only {size // 1024} KB")
        if pages is not None and pages < MIN_PAGES:
            issues.append(f"{pages} pages")

        expected = titles.get(rel)
        hits = total = None
        if expected:
            ok, hits, total = title_match(expected, first_page_text(path))
            if not ok:
                issues.append(f"title mismatch ({hits}/{total} tokens)")

        digest = md5(path)
        hashes.setdefault(digest, []).append(rel)
        if issues:
            problems.append((rel, issues))

        if not args.quiet:
            state = "OK  " if not issues else "FAIL"
            print(f"{state} {pages if pages is not None else '?':>3}p {size // 1024:6d}KB  {rel}")

    dupes = {h: v for h, v in hashes.items() if len(v) > 1}
    if not args.quiet:
        print(f"\n{len(pdfs)} PDFs, {len(problems)} with problems, {len(dupes)} duplicate set(s)")

    for rel, issues in problems:
        print(f"  PROBLEM {rel}: {'; '.join(issues)}")
    for files in dupes.values():
        print("  DUPLICATE: " + " == ".join(files))

    sys.exit(1 if problems or dupes else 0)


if __name__ == "__main__":
    main()
