---
name: code-review
description: Perform a thorough, general-purpose code review and produce a structured report. Use whenever the user asks you to review code, review a pull request or diff, check a change for bugs, look over a function or file, find issues or vulnerabilities, or give feedback on code quality — even if they don't use the exact word "review" (e.g. "take a look at this", "is this safe?", "what's wrong with this?", "could this break?").
---

# Code Review

Review code the way a thoughtful, senior engineer would: read carefully, understand the intent, and report what actually matters. Prioritize correctness and safety over style, and prefer a small number of high-signal comments over a long list of trivia.

## When to review the whole file vs. a diff

- **Diff or PR** (user gives a `git diff`, a changed file against a base, or "review this PR"): focus on what changed. Judge only the added/changed lines, plus the surrounding context needed to understand them. Don't flag pre-existing issues in untouched code unless they make the change itself unsafe.
- **Whole file or snippet** (user gives a file or pastes code): review everything, but still weight comments by impact.

## How to review

Work through these layers in order. Stop going deeper once the change is clearly understood; don't pad the review to look thorough.

1. **Understand the intent.** What is this code supposed to do? Read any accompanying description, surrounding functions, and callers. If the intent is unclear, note it as a question rather than guessing.
2. **Correctness.** Trace the logic against the intent. Look for off-by-one errors, inverted conditions, wrong variable use, missing cases, race conditions, and incorrect edge-case handling. This is the highest-value layer.
3. **Safety & security.** Injection (SQL, shell, HTML/XSS, path traversal), authentication/authorization gaps, secrets or credentials in code, unsafe deserialization, resource leaks, unbounded input, and misuse of dangerous APIs.
4. **Robustness.** Error handling, null/undefined handling, timeouts, retries, concurrency, and what happens on failure paths.
5. **Performance.** Only flag real problems with a plausible scale: accidental O(n²) in a hot path, N+1 queries, needless allocation in a loop, blocking calls in async code. Ignore micro-optimizations.
6. **Maintainability & clarity.** Naming, duplication, dead code, confusing control flow, missing comments where the *why* is non-obvious. Keep these proportionate — this layer should not dominate the review.
7. **Tests & coverage.** Missing tests for new behavior, especially edge cases and failure paths. Note untested branches only when they matter.

When unsure whether something is a real issue, say so rather than asserting. Cite the specific line(s) or file(s) for every comment so the author can find them.

## Severity levels

Assign one of these to every finding:

- **Blocker** — must fix before merge: incorrect behavior, security vulnerability, data loss/corruption, crash.
- **Major** — should fix before merge: likely bug, significant performance problem, missing error handling that causes real failures.
- **Minor** — nice to fix: readability, minor duplication, missing test for an edge case, slightly misleading name.
- **Nit** — optional polish: formatting, wording, micro-suggestions.
- **Question** — not a defect; a request for clarification about intent or a design choice.

Only use **Blocker** and **Major** for things you can defend. A review with nothing at that level is fine — say so plainly.

## Report format

Use this exact structure, in this order. Skip sections that have no content, except **Summary** and **Findings**, which are always present.

```markdown
# Code Review: <file(s) or PR title>

## Summary
One or two sentences: what the code does and an overall verdict (e.g. "Looks correct; a few minor issues." or "Has a blocking bug and needs revision."). Include the severity counts, e.g. `1 Blocker · 2 Major · 3 Minor`.

## Blocking issues
List each, prefixed with `[Blocker]`, each with file:line and a concrete fix suggestion.

## Major issues
List each, prefixed with `[Major]`, with file:line and a concrete fix suggestion.

## Minor issues
List each, prefixed with `[Minor]`.

## Nits
List each, prefixed with `[Nit]`.

## Questions
List each, prefixed with `[Question]`.

## Overall
A short closing note: the single most important thing to fix (if any), and what looks good.
```

### Finding format

Every finding follows this shape:

```
[Severity] <short title> — <file:line>

What: <one or two sentences describing the problem and why it matters.>
Fix: <a concrete, actionable suggestion. Prefer showing the corrected code inline when it's short.>
```

Keep each finding focused on one issue. If the same issue recurs in many places, call it out once and list the other locations.

## Tone

Be direct, specific, and constructive. Critique the code, not the author. Acknowledge what's done well — especially in the **Overall** section — rather than only listing problems. Avoid absolute words like "always"/"never" unless they're literally true. When you propose a change, explain the reasoning so the author can judge whether it applies to their situation.

## What not to do

- Don't rewrite the entire file or produce a full "fixed" version unless the user asks.
- Don't flag style preferences as bugs, and don't enforce a specific style guide the user hasn't asked for.
- Don't invent bugs to appear thorough. If you aren't confident, downgrade to a **Question**.
- Don't comment on code you haven't read. Read the relevant callers and context first.
