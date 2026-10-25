#!/usr/bin/env python3
"""Verify that every PDF in the library matches its citation.

Checks per file: %PDF magic, minimum size, page count, and token overlap
between the Crossref title (from the download log) and the text on page 1.
Also reports duplicate files by hash, which usually means one paper was saved
twice under different names.

With --quarantine, problem files and duplicate extras are moved out of the library
(instead of just being reported) so the library is left usable; --update-log rewrites
the download log so those records read "quarantined" rather than "ok".

Exit code is non-zero when problems are found, so it can gate a final report.

CLI:
  python verify_library.py --root ~/Papers --log download-log.json
  python verify_library.py --root ~/Papers --log download-log.json --quarantine --update-log
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
    ap.add_argument("--log", help="download-log.json (enables title verification and log update)")
    ap.add_argument("--quiet", action="store_true", help="Only print problems")
    ap.add_argument("--quarantine", nargs="?", const="_quarantine", default=None,
                    help="Move problem/duplicate files into this dir (default root/_quarantine)")
    ap.add_argument("--update-log", action="store_true",
                    help="With --quarantine, mark moved records 'quarantined' in --log")
    args = ap.parse_args()

    log_path = args.log
    titles = {}
    log_records = None
    if log_path and os.path.exists(log_path):
        log_records = json.load(open(log_path, encoding="utf-8"))
        for rec in log_records:
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
        if expected:
            ok, _, _ = title_match(expected, first_page_text(path))
            if not ok:
                issues.append("title mismatch")

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

    # Quarantine: move bad files and duplicate extras, keep the rest usable.
    moves = {}  # rel -> reason
    if args.quarantine:
        qdir = os.path.join(args.root, args.quarantine) if not os.path.isabs(args.quarantine) else args.quarantine
        os.makedirs(qdir, exist_ok=True)
        for rel, issues in problems:
            moves[rel] = "; ".join(issues)
        for files in dupes.values():
            keep = sorted(files)[0]
            for extra in files[1:]:
                moves[extra] = f"duplicate of {keep}"
        for rel, reason in moves.items():
            src = os.path.join(args.root, rel)
            dst = os.path.join(qdir, os.path.basename(rel))
            # avoid clobbering when two quarantined files share a basename
            n = 1
            while os.path.exists(dst):
                stem, ext = os.path.splitext(os.path.basename(rel))
                dst = os.path.join(qdir, f"{stem}.{n}{ext}")
                n += 1
            shutil.move(src, dst)
            print(f"  QUARANTINED {rel} -> {os.path.relpath(dst, args.root)} ({reason})")

    if args.update_log and log_records is not None and moves:
        for rec in log_records:
            if rec.get("file") and os.path.normpath(rec["file"]) in moves:
                rec["status"] = "quarantined"
                rec["quarantine_reason"] = moves[os.path.normpath(rec["file"])]
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_records, f, ensure_ascii=False, indent=1)
        print(f"updated {log_path}: {len([r for r in log_records if r.get('status') == 'quarantined'])} record(s) marked quarantined")

    sys.exit(1 if problems or dupes else 0)


if __name__ == "__main__":
    main()
