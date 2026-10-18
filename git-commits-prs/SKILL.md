---
name: git-commits-prs
description: Write Conventional Commits messages and brief pull request titles/descriptions for the current changes, and produce the exact git and GitHub CLI commands (or offer to run them). Use whenever the user asks to commit, stage, write a commit message, push, open a PR, create a pull request, squash commits, or describe their changes — even if they don't say "commit" or "PR" explicitly (e.g. "wrap this up", "ship this", "what do I write for this change?").
---

# Git Commits & Pull Requests

Help the user turn a set of changes into well-formed commits and a pull request. The deliverable is the *message text plus the exact commands* — never run anything without confirmation unless the user already asked you to.

## Workflow

1. **Inspect the changes.** Run `git status`, `git diff --staged` (fall back to `git diff` if nothing is staged), and `git log --oneline -15` to learn the repo's commit style, existing scopes, and whether the user uses Conventional Commits or a different habit.
2. **Check for a PR template.** Look for `.github/PULL_REQUEST_TEMPLATE.md` or `.github/pull_request_template.md`. If one exists, follow it; otherwise use the brief format below.
3. **Decide atomicity.** If the staged changes span unrelated concerns, propose splitting them into multiple commits (one logical change per commit). If splitting requires staging hunks, give the `git add` commands for the right files/paths. Never silently merge unrelated work into one commit — but don't over-split either; one change, one commit.
4. **Draft the commit message(s).** Follow the Conventional Commits rules below.
5. **Draft the PR title and description.** Title from the commit subject; body brief.
6. **Present everything** — message(s), PR text, and the exact commands — in one place, then ask whether to run them.

## Commit message format (Conventional Commits)

```
<type>[optional scope][!]: <subject>

[optional body]

[optional footer]
```

- **type** — one of: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`. Pick the one that best describes the *user-facing* effect.
- **scope** — optional; a short noun for the area affected (e.g. `auth`, `api`, `cli`). Use one only if it matches scopes already present in `git log` or if the change clearly belongs to one component. Omit when it adds noise.
- **`!`** — append to the type (or scope) only for breaking changes, plus a `BREAKING CHANGE:` footer explaining what breaks.
- **subject** — imperative, present tense ("add", "fix", "remove", not "added"/"fixes"). No trailing period. Concise — aim for 50 chars, never more than 72. Describe the change, not the ticket.
- **body** — optional. Use it when the *why* or the *what* isn't obvious from the subject. Wrap at 72 chars, leave a blank line after the subject.
- **footer** — for breaking changes and issue references: `BREAKING CHANGE: <what and how to migrate>`, `Closes #123`, `Refs #123`.

### Commit examples

**Fix:**
```
fix(auth): use parameterized queries in login

The login query interpolated user input directly, allowing SQL
injection. Bind parameters instead.
```

**Feature:**
```
feat(auth): add rate limiting to login endpoint

Throttle attempts per account and IP to slow brute-force attacks.
```

**Breaking change:**
```
refactor(api)!: remove /v1 endpoint

BREAKING CHANGE: /v1 is removed. Clients must migrate to /v2; the
response shape is unchanged, only the base path differs.
```

## PR title and description

**Title** — mirror the primary commit's type and subject (e.g. `feat(auth): add rate limiting to login endpoint`). If the PR contains several commits, summarize the overall change instead of copying one commit.

**Description** — keep it brief unless the repo template says otherwise. Three short sections is usually right; drop any that don't apply:

```markdown
## What
<one to three sentences on what changed>

## Why
<the motivation or problem being solved>

## Testing
<how it was verified: commands run, manual checks>
```

A one-line change may warrant a one-line PR body — don't pad it.

## Output format

Present, in this order:

```markdown
## Proposed commit(s)
<the full commit message(s), in a code block>

## Pull request
**Title:** <title>

<description, in a code block>

## Commands
git add <paths>            # only if not already staged
git commit -m "<subject>"  # or a heredoc for multi-line bodies
git push -u origin <branch>
gh pr create --title "<title>" --body "<description>"
```

Then ask the user whether to run them (or just the ones they pick). If a multi-line body is needed, show the commit as a heredoc rather than a single `-m`.

## What not to do

- Don't run `git` or `gh` commands without confirmation unless the user explicitly told you to.
- Don't force Conventional Commits if the repo clearly uses a different convention — match the existing `git log` style and say which you followed.
- Don't write "added"/"fixed" in the subject; use imperative mood.
- Don't stuff unrelated changes into a single commit to save effort; propose the split.
- Don't fabricate issue numbers or test results. Reference real numbers only if they're visible in the branch name, commit history, or the user's message.
