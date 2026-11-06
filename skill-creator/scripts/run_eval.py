#!/usr/bin/env python3
"""Run trigger evaluation for a skill description using OpenCode.

Tests whether a skill's description causes OpenCode to trigger (load the
skill) for a set of queries. Outputs results as JSON.

For every query this creates a throwaway project in a temp directory that
contains exactly one project-local skill whose description is under test,
then runs `opencode run --format json` there and watches for a `skill` tool
call. Global skills remain visible, so the candidate description competes
for the model's attention the same way it does in normal use, while the
one-skill-per-workspace isolation keeps parallel runs from seeing each
other's probes.
"""

import argparse
import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md


def make_probe_id(skill_name: str) -> str:
    """Build a unique, OpenCode-valid skill ID for the probe skill."""
    base = re.sub(r"[^a-z0-9]+", "-", skill_name.lower()).strip("-") or "skill"
    return f"{base}-skill-{uuid.uuid4().hex[:8]}"


def write_probe_skill(
    workspace: Path,
    probe_id: str,
    skill_name: str,
    skill_description: str,
) -> Path:
    """Write the skill under test into a throwaway project."""
    skill_dir = workspace / ".opencode" / "skills" / probe_id
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Folded block scalar keeps quotes, colons, and the like from breaking
    # the YAML frontmatter.
    indented_desc = "\n".join("  " + line for line in skill_description.splitlines())
    content = (
        "---\n"
        f"name: {probe_id}\n"
        "description: >-\n"
        f"{indented_desc or '  '}\n"
        "---\n\n"
        f"# {skill_name}\n\n"
        f"This skill handles: {skill_description}\n"
    )
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    return skill_dir


def _handle_event(line: str, probe_id: str) -> bool | None:
    """Return True/False once triggering is decided, otherwise None."""
    line = line.strip()
    if not line:
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None

    if event.get("type") != "tool_use":
        return None

    part = event.get("part") or {}
    if part.get("tool") != "skill":
        # Other tools (read, glob, bash, ...) do not decide the outcome; the
        # model may still load a skill on a later step.
        return None

    state = part.get("state") or {}
    loaded_id = str((state.get("input") or {}).get("id", ""))
    return loaded_id == probe_id


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    model: str | None = None,
    workspace: str | None = None,
) -> bool:
    """Run a single query and return whether the skill was triggered.

    Each run gets its own workspace (and therefore its own advertised skill
    set) so concurrent evaluations cannot interfere with each other.
    """
    probe_id = make_probe_id(skill_name)
    owns_workspace = workspace is None
    workspace_path = (
        Path(tempfile.mkdtemp(prefix="opencode-skill-eval-"))
        if owns_workspace
        else Path(workspace).resolve()
    )
    probe_dir = None

    try:
        workspace_path.mkdir(parents=True, exist_ok=True)
        probe_dir = write_probe_skill(
            workspace_path, probe_id, skill_name, skill_description
        )

        cmd = ["opencode", "run", "--format", "json", "--auto"]
        if model:
            cmd.extend(["--model", model])
        cmd.extend(["--title", f"skill-eval {probe_id}"])
        cmd.append(query)

        # `--auto` keeps permission prompts from blocking a non-interactive
        # run; trigger evaluation only needs the skill tool, which is allowed
        # by default anyway.
        #
        # PWD must be updated alongside `cwd`: OpenCode uses the environment's
        # PWD to resolve the project location, and subprocess cwd changes do
        # not touch it.
        env = {**os.environ, "PWD": str(workspace_path)}

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=str(workspace_path),
            env=env,
            start_new_session=True,
        )

        buffer = ""
        deadline = time.time() + timeout

        try:
            while time.time() < deadline:
                if process.poll() is not None:
                    remaining = process.stdout.read() if process.stdout else b""
                    if remaining:
                        buffer += remaining.decode("utf-8", errors="replace")
                    break

                ready, _, _ = select.select([process.stdout], [], [], 1.0)
                if not ready:
                    continue

                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    decision = _handle_event(line, probe_id)
                    if decision is not None:
                        return decision

            decision = _handle_event(buffer, probe_id)
            return bool(decision)
        finally:
            # Kill on every exit path: early return, exception, or timeout.
            if process.poll() is None:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    process.kill()
                process.wait()
    finally:
        if probe_dir is not None:
            shutil.rmtree(probe_dir, ignore_errors=True)
        if owns_workspace:
            shutil.rmtree(workspace_path, ignore_errors=True)


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for opencode run, as provider/model (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
