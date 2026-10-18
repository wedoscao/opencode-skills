# opencode-skills

A collection of [opencode](https://opencode.ai) skills.

## Skills

| Skill | Description |
| --- | --- |
| [`brainstorming`](brainstorming/SKILL.md) | Helps generate and explore ideas, think through a problem from multiple angles, and converge on a decision. Triggers when asked to ideate, spitball, weigh options, get unstuck, play devil's advocate, or pressure-test a plan. |
| [`code-review`](code-review/SKILL.md) | Performs a thorough, general-purpose code review and produces a structured report. Triggers when asked to review code, a pull request or diff, look for bugs or vulnerabilities, or give feedback on code quality. |
| [`git-commits-prs`](git-commits-prs/SKILL.md) | Writes Conventional Commits messages and brief pull request titles/descriptions for the current changes, and produces the exact git and GitHub CLI commands to run them. |
| [`skill-creator`](skill-creator/SKILL.md) | Creates new skills, modifies and improves existing ones, and measures skill performance via evals and benchmarks. |

Each skill directory contains a `SKILL.md` with its instructions. Skills that
ship evals also include an `evals/evals.json` fixture file.

## Installation

Copy the skill directories into your opencode skills directory:

```bash
git clone git@github.com:wedoscao/opencode-skills.git /tmp/opencode-skills
cp -r /tmp/opencode-skills/brainstorming \
      /tmp/opencode-skills/code-review \
      /tmp/opencode-skills/git-commits-prs \
      /tmp/opencode-skills/skill-creator \
      ~/.config/opencode/skills/
```

Or copy a single skill:

```bash
cp -r /tmp/opencode-skills/code-review ~/.config/opencode/skills/
```

opencode picks up skills from `~/.config/opencode/skills/` automatically — no
additional configuration is required.

## Development

The `*-workspace/` directories that appear while running evals are generated
artifacts from the `skill-creator` workflow and are git-ignored.
