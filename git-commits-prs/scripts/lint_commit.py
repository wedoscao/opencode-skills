#!/usr/bin/env python3
"""Lint a draft commit message against Conventional Commits and repo style.

The rules here are mechanical and worth enforcing before the agent shows the user a
message: valid type, subject length, no trailing period, imperative hint, `!` requires
a BREAKING CHANGE footer, and body/footer lines wrapped at 72.

CLI:
  python lint_commit.py --file msg.txt [--allowed-types feat,fix,chore] [--max-subject 72]
  echo "fix(auth): use parameterized queries" | python lint_commit.py -
"""
import argparse
import re
import sys

CC_TYPES = {"feat", "fix", "docs", "style", "refactor", "perf", "test",
            "build", "ci", "chore", "revert"}

HEADER_RE = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?: (?P<subj>.+)$")
# Verbs that strongly suggest past tense; a coarse heuristic, not a hard rule.
PAST_HINT = re.compile(r"^(added|fixed|removed|updated|changed|renamed|refactored|deleted|implemented|created)\b", re.I)


def lint(message, allowed_types=None, max_subject=72, max_line=72):
    problems = []
    allowed = set(allowed_types) if allowed_types else CC_TYPES
    lines = [ln.rstrip("\n") for ln in message.splitlines()]
    if not lines:
        return ["empty message"]

    header = lines[0].strip()
    m = HEADER_RE.match(header)
    if not m:
        problems.append("subject is not '<type>[scope][!]: <subject>'")
    else:
        typ = m.group("type")
        if typ not in allowed:
            problems.append(f"type '{typ}' not in allowed types: {', '.join(sorted(allowed))}")
        subj = m.group("subj")
        if len(lines[0]) > max_subject:
            problems.append(f"subject is {len(lines[0])} chars (max {max_subject})")
        if subj.endswith("."):
            problems.append("subject must not end with a period")
        if subj and not subj[0].islower() and not subj[0].isdigit():
            problems.append("subject should start lowercase (imperative mood)")
        if PAST_HINT.match(subj):
            problems.append(f"subject looks past tense ('{subj.split()[0]}'); use imperative")

    if len(lines) > 1 and lines[1].strip():
        problems.append("blank line required between subject and body")

    has_break = any("BREAKING CHANGE:" in ln for ln in lines)
    has_bang = bool(m and m.group("bang"))
    if has_bang and not has_break:
        problems.append("breaking change ('!') needs a 'BREAKING CHANGE:' footer")

    for i, ln in enumerate(lines[1:], start=2):
        if len(ln) > max_line:
            problems.append(f"line {i} is {len(ln)} chars (wrap at {max_line})")

    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", default="-", help="File to lint, or '-' for stdin (default -)")
    ap.add_argument("--file", dest="file", help="File to lint (alias for the positional input)")
    ap.add_argument("--allowed-types", help="Comma list, e.g. feat,fix,chore (default: standard set)")
    ap.add_argument("--max-subject", type=int, default=72)
    ap.add_argument("--max-line", type=int, default=72)
    args = ap.parse_args()

    path = args.file or args.input
    if path == "-":
        text = sys.stdin.read()
    else:
        with open(path, encoding="utf-8") as f:
            text = f.read()

    allowed = [t.strip() for t in args.allowed_types.split(",")] if args.allowed_types else None
    problems = lint(text, allowed, args.max_subject, args.max_line)
    if problems:
        print("FAIL")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
