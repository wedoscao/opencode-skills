#!/usr/bin/env python3
"""Gather everything a commit/PR message needs from a git repo, deterministically.

This replaces the agent re-typing `git status` / `git diff` / `git log` every time and
re-inferring the repo's commit convention from scratch. It collects:

  - current branch
  - status (short)
  - staged vs unstaged changes (stat + full diff on request)
  - the last 15 commits (style + existing scopes)
  - a detection of whether the repo uses Conventional Commits, and which types/scopes
    actually appear (so the message matches the repo instead of forcing a habit)
  - whether a PR template exists

CLI:
  python inspect_repo.py [--repo .] [--diff] [--context 3] [--out inspect.json]
"""
import argparse
import json
import os
import re
import subprocess
import sys

CC_TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test",
            "build", "ci", "chore", "revert")
CC_RE = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?: (?P<subj>.+)")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True)


def lines(out):
    return [ln for ln in out.splitlines() if ln.strip()]


def detect_convention(repo):
    """Return (uses_conventional, {type: count}, {scope: count}) from recent history."""
    out = git(repo, "log", "--no-merges", "-n", "100", "--format=%s")
    subjects = lines(out.stdout)
    types, scopes, cc = {}, {}, 0
    for s in subjects:
        m = CC_RE.match(s.strip())
        if m:
            cc += 1
            types[m.group("type")] = types.get(m.group("type"), 0) + 1
            if m.group("scope"):
                scopes[m.group("scope")] = scopes.get(m.group("scope"), 0) + 1
    uses = cc > 0 and cc >= len(subjects) * 0.5
    return uses, types, scopes, subjects


def find_pr_template(repo):
    candidates = [
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/pull_request_template.md",
        "PULL_REQUEST_TEMPLATE.md",
        "docs/PULL_REQUEST_TEMPLATE.md",
        ".github/PULL_REQUEST_TEMPLATE/",
    ]
    for c in candidates:
        p = os.path.join(repo, c)
        if os.path.exists(p):
            return c
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="Path to the repository (default .)")
    ap.add_argument("--diff", action="store_true", help="Include the full staged+unstaged diff")
    ap.add_argument("--context", type=int, default=3, help="Diff context lines (default 3)")
    ap.add_argument("--out", help="Write a JSON summary here")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        sys.exit(2)

    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "(detached)"
    status = lines(git(repo, "status", "--short").stdout)
    staged_stat = git(repo, "diff", "--staged", "--stat").stdout.strip()
    unstaged_stat = git(repo, "diff", "--stat").stdout.strip()
    uses_cc, types, scopes, recent = detect_convention(repo)
    template = find_pr_template(repo)

    report = []
    report.append(f"# Repo inspection — {repo}")
    report.append("")
    report.append(f"**Branch:** `{branch}`")
    report.append("")
    report.append(f"**Convention:** {'Conventional Commits' if uses_cc else 'not obviously Conventional Commits'}")
    if types:
        report.append("**Types in use:** " + ", ".join(f"{t}({n})" for t, n in sorted(types.items(), key=lambda x: -x[1])))
    if scopes:
        report.append("**Scopes in use:** " + ", ".join(f"{s}({n})" for s, n in sorted(scopes.items(), key=lambda x: -x[1])))
    report.append("")
    report.append("## Status")
    if status:
        report.extend("  " + s for s in status)
    else:
        report.append("  (clean working tree)")
    report.append("")
    if staged_stat:
        report.append("## Staged")
        report.append("```\n" + staged_stat + "\n```")
        report.append("")
    if unstaged_stat:
        report.append("## Unstaged")
        report.append("```\n" + unstaged_stat + "\n```")
        report.append("")
    report.append("## Recent commits")
    report.append("```\n" + "\n".join(recent[:15]) + "\n```")
    report.append("")
    report.append(f"**PR template:** {template or 'none found'}")
    report.append("")
    if args.diff:
        diff = git(repo, "diff", "--staged", f"-U{args.context}").stdout
        diff += git(repo, "diff", f"-U{args.context}").stdout
        if diff.strip():
            report.append("## Diff (staged + unstaged)")
            report.append("```diff\n" + diff + "\n```")

    text = "\n".join(report)
    print(text)

    if args.out:
        summary = {
            "repo": repo,
            "branch": branch,
            "status": status,
            "uses_conventional_commits": uses_cc,
            "types": types,
            "scopes": scopes,
            "pr_template": template,
            "recent_commits": recent[:15],
        }
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=1)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
