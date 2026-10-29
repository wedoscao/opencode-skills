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
| [`presentations`](presentations/SKILL.md) | Creates, edits, reads, and inspects PowerPoint decks (.pptx/.potx): building slide decks, extracting text, restyling existing presentations, working with templates, layouts, notes, or comments, and splitting/merging decks. |
| [`research-roadmap`](research-roadmap/SKILL.md) | Turns a research direction into an executable plan: gap analysis, research questions, experiment matrix, sprint schedule with gates, and a target venue shortlist. |
| [`scientific-researcher`](scientific-researcher/SKILL.md) | Researches a scientific question end-to-end: searches for and discovers literature, evaluates source quality and evidence strength, and synthesizes findings into a cited summary or literature review. |
| [`skill-creator`](skill-creator/SKILL.md) | Creates new skills, modifies and improves existing ones, and measures skill performance via evals and benchmarks. |
| [`vietnamese-translator`](vietnamese-translator/SKILL.md) | Translates text into fluent Vietnamese while keeping technical terms, code identifiers, and product names in English, preserving Markdown and code formatting. |

> `dtk-god/` is a personal, local-only skill and is git-ignored; it is not listed here.

Each skill directory contains a `SKILL.md` with its instructions. Skills that
ship evals also include an `evals/evals.json` fixture file. Skills with
deterministic or repetitive steps ship a `scripts/` directory and reference the
scripts from `SKILL.md`.

## Ported from mattpocock/skills

27 skills ported from [Matt Pocock's `skills`](https://github.com/mattpocock/skills), grouped under `engineering/` and `productivity/`. Matt's original `code-review` (two-axis Standards + Spec review) is installed as **`code-review-2axis`** so it does not shadow the general-purpose `code-review` above.

### Engineering

**User-invoked**

| Skill | What it does |
| --- | --- |
| [`ask-matt`](engineering/ask-matt/SKILL.md) | Router: ask which skill or flow fits your situation |
| [`grill-with-docs`](engineering/grill-with-docs/SKILL.md) | Grilling session that also builds the domain model (glossary + ADRs) |
| [`triage`](engineering/triage/SKILL.md) | Move issues/PRs through triage roles, write agent-ready briefs |
| [`improve-codebase-architecture`](engineering/improve-codebase-architecture/SKILL.md) | Scan for deepening opportunities, render an HTML report, grill through a pick |
| [`setup-matt-pocock-skills`](engineering/setup-matt-pocock-skills/SKILL.md) | One-time per-repo setup (issue tracker, labels, doc layout) |
| [`to-spec`](engineering/to-spec/SKILL.md) | Turn the conversation into a spec, publish to the tracker |
| [`to-tickets`](engineering/to-tickets/SKILL.md) | Break a plan/spec into tracer-bullet tickets with blocking edges |
| [`implement`](engineering/implement/SKILL.md) | Build from a spec/tickets, driving `tdd`, closing with `code-review-2axis` |
| [`implement-spec`](engineering/implement-spec/SKILL.md) | Implement a whole spec on one branch via parallel implementer subagents |
| [`wayfinder`](engineering/wayfinder/SKILL.md) | Plan huge work as a shared map of decision tickets |
| [`retro`](engineering/retro/SKILL.md) | Suggest environment improvements after a session |

**Model-invoked**

| Skill | What it does |
| --- | --- |
| [`prototype`](engineering/prototype/SKILL.md) | Throwaway prototype to answer a design question |
| [`diagnosing-bugs`](engineering/diagnosing-bugs/SKILL.md) | Disciplined diagnosis loop: feedback loop, minimise, hypothesise, fix |
| [`research`](engineering/research/SKILL.md) | Investigate a question against primary sources, write a cited file |
| [`tdd`](engineering/tdd/SKILL.md) | Red-green-refactor, one vertical slice at a time |
| [`domain-modeling`](engineering/domain-modeling/SKILL.md) | Build/sharpen the domain model; update glossary + ADRs |
| [`codebase-design`](engineering/codebase-design/SKILL.md) | Deep-module design vocabulary (module, interface, seam, adapter, …) |
| [`code-review-2axis`](engineering/code-review-2axis/SKILL.md) | Two-axis diff review (Standards + Spec) via parallel subagents |
| [`pr`](engineering/pr/SKILL.md) | The shape of a good PR body |
| [`wizard`](engineering/wizard/SKILL.md) | Generate an interactive bash wizard for human-only steps |

### Productivity

**User-invoked**

| Skill | What it does |
| --- | --- |
| [`grill-me`](productivity/grill-me/SKILL.md) | Relentless interview to sharpen a plan/design |
| [`handoff`](productivity/handoff/SKILL.md) | Compact the conversation into a handoff document |
| [`teach`](productivity/teach/SKILL.md) | Teach a concept over multiple sessions in a stateful workspace |
| [`to-questionnaire`](productivity/to-questionnaire/SKILL.md) | Turn a decision you can't answer into a questionnaire for someone who can |
| [`wait-what`](productivity/wait-what/SKILL.md) | Re-pitch a message that didn't land |

**Model-invoked**

| Skill | What it does |
| --- | --- |
| [`grilling`](productivity/grilling/SKILL.md) | The interview primitive behind grill-me / grill-with-docs / triage / wayfinder |
| [`writing-for-agents`](productivity/writing-for-agents/SKILL.md) | How to write documents agents consume (skills, AGENTS.md, pointed-at docs) |

## Ported from K-Dense-AI/scientific-agent-skills

56 skills ported from [K-Dense's Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills), grouped under `k-dense/`. Two sets: field-independent research workflow skills, and ML/AI + data-analysis package skills. Each lives at `k-dense/<name>/SKILL.md`.

### Research workflow (35)

`paper-lookup`, `literature-review`, `paperclip`, `bgpt-paper-search`, `paperzilla`, `exa-search`, `parallel-web`, `research-lookup`, `database-lookup`, `ontology-term-resolution`, `scientific-critical-thinking`, `scholar-evaluation`, `peer-review`, `scientific-writing`, `citation-management`, `pyzotero`, `venue-templates`, `scientific-slides`, `latex-posters`, `pptx-posters`, `scientific-schematics`, `infographics`, `markdown-mermaid-writing`, `scientific-visualization`, `generate-image`, `hypothesis-generation`, `scientific-brainstorming`, `experimental-design`, `statistical-power`, `statistical-analysis`, `uncertainty-and-units`, `exploratory-data-analysis`, `research-grants`, `what-if-oracle`, `consciousness-council`

### ML/AI and data (21)

`pytorch-lightning`, `transformers`, `stable-baselines3`, `pufferlib`, `scikit-learn`, `scikit-survival`, `shap`, `aeon`, `timesfm-forecasting`, `pymc`, `pymoo`, `torch-geometric`, `umap-learn`, `statsmodels`, `dask`, `polars`, `vaex`, `matplotlib`, `seaborn`, `networkx`, `optimize-for-gpu`

Some skills need external credentials or CLIs to run — `exa-search` (Exa), `parallel-web` (Parallel), `bgpt-paper-search` (BGPT), `paperzilla` (`pz` CLI), `paperclip` (GXL CLI + auth), and the image/diagram skills (`generate-image`, `infographics`, `scientific-schematics`, via OpenRouter). The rest run locally once their Python dependencies are installed.

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
