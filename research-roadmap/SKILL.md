---
name: research-roadmap
description: Turn a research direction into an executable plan — gap analysis, research questions, contribution shaping, experiment matrix, sprint schedule with go/no-go gates, target venue shortlist, and risk register. Use this whenever the user wants a research roadmap, a study plan, a thesis or dissertation plan, a proposal or đề cương, wants to turn an idea into publishable work, asks "làm sao để ra bài", "lập kế hoạch nghiên cứu", "kế hoạch làm KLTN", "đề cương nghiên cứu", "nên bắt đầu từ đâu", "chia việc mấy tháng", or needs to choose between venues/targets. Also use when they have a paper library or a list of papers and ask what to do next, or when a plan exists but has no experiments, no gates, or no risks.
---

# Research Roadmap

Convert "I want to work on X" into a plan someone could actually follow on Monday morning.

The failure this skill prevents is the plan that looks serious and decides nothing: a topic sentence, a vague timeline, "read papers" as a milestone, and no way to know at month three whether to continue. A roadmap earns its name by making the next two weeks concrete and by making it cheap to stop.

## Workflow

### 1. Intake — six questions, no more

Ask together, not one at a time:

| Question | Why it changes the plan |
|---|---|
| Direction, in one sentence | Everything downstream derives from it |
| Months available | Decides which target profile is realistic |
| Compute | Rules out ideas that need 8×A100 |
| Data access (public / permission needed / already have) | Medical and industrial data is the usual blocker |
| Current level (never trained a model / comfortable / has published) | Sets baseline count and gate strictness |
| Goal: graduate, publish, scholarship, grant | Chooses between speed and depth |

If the user has a paper library (from the `paper-library` skill or a folder of PDFs), read its `README.md`/`INDEX.md` first. A roadmap built on papers the user has actually downloaded is far more credible than one built on memory.

If a user cannot answer something, record the assumption in the document instead of blocking. Mark it `(giả định)`. A visible assumption can be corrected; a silent one becomes a broken plan.

### 2. Choose the target profile

Profiles live in `references/targets.json`; each sets the minimum number of baselines, datasets, ablations, seeds, and whether statistical testing is required.

| Key | Target | Typical months |
|---|---|---|
| `thesis` | Đồ án / KLTN | 4–6 |
| `conf-domestic` | Hội nghị trong nước (KSE, SoICT) | 5–7 |
| `conf-intl` | Hội nghị quốc tế A/A* | 9–15 |
| `journal-q1q2` | Tạp chí Q1–Q2 | 10–18 |
| `journal-q3q4` | Tạp chí Q3–Q4 | 6–10 |
| `grant` | Đề tài NCKH / grant | 6–12 |

If the user has not chosen, infer from constraints and say why in one line: `(chọn: 9 tháng + có GPU → journal-q1q2)`. Never silently default to the most ambitious profile — an over-scoped plan is how students lose a year.

### 3. Scaffold, then actually fill it

```bash
python scripts/scaffold.py --intent intent.json --out ./roadmap
```

This writes seven files: `PROPOSAL.md`, `GAP-TABLE.csv`, `EXPERIMENTS.md`, `TARGET.md`, `ROADMAP.md`, `RISKS.md`, `OUTLINE.md`.

**The scaffold is the floor, not the deliverable.** Leaving `TODO` everywhere and handing it over is a failure. Fill it, in this order:

0. **Check coverage before anything else.** Count how many papers in the library are actually in the sub-area (audio deepfake ≠ face deepfake, LLM evaluation ≠ LLM application). If fewer than ~6, stop and fetch more with the `paper-library` skill. A gap table built on adjacent-domain papers produces analogies ("voice has no blending boundary") that a reviewer will dismantle. Say so in the document if you proceed anyway.
1. **`GAP-TABLE.csv`** — one row per paper: problem, method, *the limitation the authors admit*, and where you fit. The third column is the only one that produces novelty; if you cannot quote it, you have not read the paper.
2. **`PROPOSAL.md`** — three to five gaps that repeat across papers become your problem statement. One RQ, answerable by an experiment. Contributions equal to the profile's requirement, each tied to a table or figure.
3. **`EXPERIMENTS.md`** — datasets with access status, baselines with code availability, the main matrix, ablations, metrics, seeds, GPU-hour budget.
4. **`TARGET.md`** — venue shortlist from `scripts/venue_check.py`, scope fit judged by you, plus the quartile caveat.
5. **`RISKS.md`** — risks with an early-warning signal and a concrete fallback, not "be careful".

### 4. Check for a scoop before committing

```bash
python scripts/scoop_check.py --query "idea in one sentence" --months 12 --out SCOOP.md
```

Title-overlap is a coarse filter, not proof. Read the abstract of anything above 0.5. The question is not "has anyone worked on this area" (always yes) but "has anyone already answered *this* question with *this* evidence". If they have, change the angle rather than the topic.

### 5. Sanity-check the schedule

`ROADMAP.md` is generated with two-week sprints and a gate at each phase boundary: reproduce baselines, main results, ablations, writing, submission. Gates are decision points, not ceremonies. Write into the document what happens if a gate fails — narrowing the claim, swapping a baseline, or changing the question. A plan with no branch for failure is a wish.

Budget reality: phase 3 (main experiments) is where schedules die. If the timeline gives it less than 30% of the total, rebalance.

### 6. Deliver with an honest summary

Report, in the user's language: the chosen profile and why, the one-sentence RQ, the number of baselines/datasets required, the biggest risk, and the first two weeks of work. Flag every assumption you made. Do not claim a venue is Q1/Q2 — say what was checked and what the user must verify.

## Definition of done

The roadmap is finished when a reader can answer all of these without asking you:

- What exactly is the claim, and which experiment proves it?
- For each hypothesis: what result would **falsify** it? (A hypothesis with no falsification criterion is a wish.)
- Which baseline, on which dataset, with how many seeds?
- What happens at month 3 if results do not beat the baseline?
- Which venue, what page limit, what is the fallback?
- What are the next five working days?

If any answer is missing, the file is a template, not a plan.

Gate it mechanically before handing over: `python scripts/check_plan.py --dir ./roadmap [--target <key>] [--library <papers-root>]`. It fails on leftover `TODO`s, an unfilled RQ1, too few baselines/datasets for the target, an empty venue table, and a missing falsification criterion — the same checklist as above, checked by a script instead of eyeballing.

## Honest limits

- **Quartile cannot be verified here.** Scopus/JCR are subscription sources that change yearly. `venue_check.py` checks ISSN, publisher, DOAJ and APC only.
- **No results are invented.** Experiment tables stay empty until the user runs them.
- **A roadmap is not a guarantee.** It buys the ability to notice failure early, not immunity from it.
- **Advisor fit matters more than any document.** The plan should end with "show this to your advisor before committing dates", and the user should ask about the group's recent publication record.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/scaffold.py` | Seven-file skeleton from an intent JSON, profile-aware |
| `scripts/timeline.py` | Sprint table with gates from a month budget |
| `scripts/scoop_check.py` | Recent Crossref + arXiv work ranked by title overlap |
| `scripts/venue_check.py` | ISSN, publisher, DOAJ status, APC; explicit about what it cannot check |
| `scripts/check_plan.py` | Definition-of-done gate: TODOs, RQ1, baseline/dataset counts, falsification, risks |

## Worked example

A 5-month thesis on Vietnamese deepfake detection, run through this skill, produced: a decision to
treat "deepfake" as **audio** (dataset and ethics constraints, stated as an assumption), 11 gap rows
with quoted author limitations, four hypotheses each with a falsification threshold, a speaker-disjoint
split rule, a GPU budget derived from run counts, and an explicit refusal to claim SOTA or a new
dataset because the scoop check found VSASV/SEA-Spoof/VLSP already occupying those positions.
That refusal is the skill working: the interesting contribution became calibration and risk-controlled
abstention, not "a Vietnamese benchmark".
