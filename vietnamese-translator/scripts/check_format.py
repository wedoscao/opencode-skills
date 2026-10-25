#!/usr/bin/env python3
"""Check that a translation preserved the parts a machine can verify, byte for byte.

Translation quality is human judgement, but "did the code blocks survive untouched?"
"are all the inline code tokens and URLs still there?" and "does the Vietnamese actually
carry diacritics?" are mechanical — and exactly the things a translator misses under
pressure. This turns the skill's manual "Review" step into a cheap, repeatable gate.

CLI:
  python check_format.py --source src.md --target vi.md
  python check_format.py --source src.md --target vi.md --report report.txt
"""
import argparse
import re
import sys

CODE_FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
INLINE_CODE = re.compile(r"`([^`\n]+)`")
URL = re.compile(r"https?://[^\s)>`\"]+")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HEADING = re.compile(r"^(#{1,6})\s", re.M)
VI_DIACRITICS = "ăâđêôơưĂÂĐÊÔƠƯ" + "áàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"


def fence_blocks(text):
    return CODE_FENCE.findall(text)


def inline_set(text):
    return set(INLINE_CODE.findall(text))


def url_set(text):
    urls = set(URL.findall(text))
    urls |= set(MD_LINK.findall(text))
    return urls


def heading_seq(text):
    return [m.group(1) for m in HEADING.finditer(text)]


def table_rows(text):
    rows = []
    for ln in text.splitlines():
        if ln.strip().startswith("|") and not re.match(r"^\s*\|[\s:\-|]+\|\s*$", ln):
            rows.append(ln)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--report", help="Write the report here instead of stdout")
    args = ap.parse_args()

    src = open(args.source, encoding="utf-8").read()
    tgt = open(args.target, encoding="utf-8").read()

    problems = []

    sf, tf = fence_blocks(src), fence_blocks(tgt)
    if sf != tf:
        problems.append(f"fenced code blocks differ: {len(sf)} in source vs {len(tf)} in target")

    miss_inline = inline_set(src) - inline_set(tgt)
    if miss_inline:
        problems.append(f"missing inline code tokens: {sorted(miss_inline)[:8]}")

    miss_url = url_set(src) - url_set(tgt)
    if miss_url:
        problems.append(f"missing URLs: {sorted(miss_url)[:8]}")

    if heading_seq(src) != heading_seq(tgt):
        problems.append("heading structure changed (levels/count differ)")

    if len(table_rows(src)) != len(table_rows(tgt)):
        problems.append(f"table row count differs: {len(table_rows(src))} vs {len(table_rows(tgt))}")

    # Diacritics heuristic: Vietnamese prose should contain marked vowels; if the
    # target is all-ASCII it was probably stripped or left in English.
    if any(ch in VI_DIACRITICS for ch in tgt):
        pass
    else:
        problems.append("no Vietnamese diacritics found in target — verify it was actually translated")

    lines = []
    if problems:
        lines.append("FAIL")
        lines += [f"  - {p}" for p in problems]
    else:
        lines.append("OK — code blocks, inline code, URLs, headings and table shape preserved")
    lines.append(f"  ({len(sf)} code blocks, {len(inline_set(src))} inline tokens, "
                 f"{len(url_set(src))} urls, {len(table_rows(src))} table rows)")

    report = "\n".join(lines)
    if args.report:
        open(args.report, "w", encoding="utf-8").write(report + "\n")
        print(f"wrote {args.report}")
    print(report)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
