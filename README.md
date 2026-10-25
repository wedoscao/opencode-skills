# opencode-skills

A collection of [opencode](https://opencode.ai) skills.

## Skills

| Skill | Description |
| --- | --- |
| [`brainstorming`](brainstorming/SKILL.md) | Helps generate and explore ideas, think through a problem from multiple angles, and converge on a decision. Triggers when asked to ideate, spitball, weigh options, get unstuck, play devil's advocate, or pressure-test a plan. |
| [`code-review`](code-review/SKILL.md) | Performs a thorough, general-purpose code review and produces a structured report. Triggers when asked to review code, a pull request or diff, look for bugs or vulnerabilities, or give feedback on code quality. |
| [`git-commits-prs`](git-commits-prs/SKILL.md) | Writes Conventional Commits messages and brief pull request titles/descriptions for the current changes, and produces the exact git and GitHub CLI commands to run them. |
| [`paper-library`](paper-library/SKILL.md) | Builds a curated, verified PDF library of peer-reviewed papers for one or more research directions, prioritizing Scopus/Web of Science venues. |
| [`paper-reader`](paper-reader/SKILL.md) | Reads, summarizes, critiques, and extracts structured information from scientific papers, and explains them in plain language. Handles PDFs, arXiv/DOI/PubMed links, and pasted text, and compares multiple papers. |
| [`research-roadmap`](research-roadmap/SKILL.md) | Turns a research direction into an executable plan: gap analysis, research questions, experiment matrix, sprint schedule with gates, and a target venue shortlist. |
| [`scientific-researcher`](scientific-researcher/SKILL.md) | Researches a scientific question end-to-end: searches for and discovers literature, evaluates source quality and evidence strength, and synthesizes findings into a cited summary or literature review. |
| [`skill-creator`](skill-creator/SKILL.md) | Creates new skills, modifies and improves existing ones, and measures skill performance via evals and benchmarks. |
| [`vietnamese-translator`](vietnamese-translator/SKILL.md) | Translates text into fluent Vietnamese while keeping technical terms, code identifiers, and product names in English, preserving Markdown and code formatting. |

> `dtk-god/` is a personal, local-only skill and is git-ignored; it is not listed here.

Each skill directory contains a `SKILL.md` with its instructions. Skills that
ship evals also include an `evals/evals.json` fixture file. Skills with
deterministic or repetitive steps ship a `scripts/` directory and reference the
scripts from `SKILL.md`.

## Installation

Copy the skill directories into your opencode skills directory:

```bash
git clone git@github.com:wedoscao/opencode-skills.git /tmp/opencode-skills
cp -r /tmp/opencode-skills/*/ ~/.config/opencode/skills/
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
