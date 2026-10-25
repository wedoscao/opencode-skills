#!/usr/bin/env python3
"""Gather the review context a code review needs, deterministically.

The review judgement stays with the agent; this only does the mechanical part that is
otherwise re-typed (and often mis-typed) every time: the changed-file list, each file's
diff with line numbers and context, and a guess at the repo's test/lint commands so the
reviewer can suggest running them.

CLI:
  python collect_context.py [--repo .] [--base main] [--context 6] [--paths a.py b.py] [--out bundle.md]
"""
import argparse
import os
import re
import subprocess
import sys


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def changed_files(repo, base):
    cmd = ["diff", "--name-only"]
    if base:
        cmd += [f"{base}...HEAD"]
    else:
        cmd += ["HEAD", "--"]  # uncommitted + staged vs HEAD
    out = git(repo, *cmd).stdout
    return [ln for ln in out.splitlines() if ln.strip()]


def detect_commands(repo):
    """Guess how to run tests/lint from common config files."""
    found = []
    package = os.path.join(repo, "package.json")
    if os.path.exists(package):
        try:
            import json
            data = json.load(open(package, encoding="utf-8"))
            scripts = data.get("scripts") or {}
            for k in ("test", "lint", "typecheck", "build"):
                if scripts.get(k):
                    found.append(f"npm run {k}")
        except Exception:
            pass
    for marker, cmd in [
        ("pyproject.toml", "pytest"),
        ("pytest.ini", "pytest"),
        ("tox.ini", "pytest"),
        ("Makefile", "make test"),
        ("Cargo.toml", "cargo test"),
        ("go.mod", "go test ./..."),
    ]:
        if os.path.exists(os.path.join(repo, marker)):
            found.append(cmd)
    return found


def diff_for(repo, path, base, context):
    parts = []
    if base:
        d = git(repo, "diff", f"-U{context}", f"{base}...HEAD", "--", path).stdout
    else:
        d = git(repo, "diff", f"-U{context}", "HEAD", "--", path).stdout
        d += git(repo, "diff", f"-U{context}", "--", path).stdout
    if d.strip():
        parts.append(d)
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="Path to the repository (default .)")
    ap.add_argument("--base", default=None, help="Base ref to diff against (e.g. main)")
    ap.add_argument("--context", type=int, default=6, help="Diff context lines (default 6)")
    ap.add_argument("--paths", nargs="*", help="Restrict to these files instead of autodetecting")
    ap.add_argument("--out", help="Write the bundle here instead of stdout")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        sys.exit(2)

    files = args.paths or changed_files(repo, args.base)
    if not files:
        print("no changed files detected (try --paths)", file=sys.stderr)
        sys.exit(1)

    cmds = detect_commands(repo)
    out = []
    out.append("# Review context")
    out.append("")
    out.append(f"**Repo:** {repo}")
    out.append(f"**Base:** {args.base or 'HEAD (staged + unstaged)'}")
    out.append(f"**Changed files ({len(files)}):**")
    for f in files:
        out.append(f"  - {f}")
    if cmds:
        out.append("")
        out.append("**Detected test/lint commands:** " + ", ".join(f"`{c}`" for c in cmds))
    out.append("")

    for f in files:
        d = diff_for(repo, f, args.base, args.context)
        if not d.strip():
            continue
        out.append(f"## {f}")
        out.append("```diff")
        out.append(d)
        out.append("```")
        out.append("")

    text = "\n".join(out)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
