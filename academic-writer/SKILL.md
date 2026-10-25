---
name: academic-writer
description: Write academic papers, conference submissions, and theses (KLTN/đồ án/luận văn) in Vietnamese or English. Use whenever the user wants to draft or polish a paper, "viết bài báo", "viết KLTN", "viết luận văn", "viết đề cương", write an abstract/intro/method/experiments/conclusion, or turn results into a submission-ready manuscript with claim-evidence mapping and a reviewer stress test.
---

# Academic Writer

Turn results and an outline into a submission-ready manuscript in Vietnamese or English, where every claim is attached to evidence and the structure matches the venue.

The failure mode this skill prevents is the *beautiful but unsupported* paper: fluent prose whose claims float free of any table or figure, a contribution section that promises more than the experiments show, a related-work section that lists papers without saying where you differ, and register that flips between formal and casual. This skill is not about word count; it is about making each sentence provable.

## First decision: language and target

Establish both before writing a word:

1. **Language** — Vietnamese or English. This changes every convention below. Ask, or infer from the venue (VLSP/SoICT/KSE → often Vietnamese; ACL/EMNLP/AAAI → English; KLTN at a Vietnamese university → usually Vietnamese, sometimes English allowed).
2. **Target** — domestic conference (6–8 pages), international conference, journal, or thesis (KLTN/đồ án/luận văn). This sets page budget, structure depth, and how much related work to carry.

If either is unknown, state the assumption in one line and let the user correct it.

## Workflow

### 1. Load the material, never write from memory

Read the inputs that exist: `OUTLINE.md`, `PROPOSAL.md`, `EXPERIMENTS.md`, result tables (`RESULTS.md` / `EXPERIMENTS.md`), and the paper library's `GAP-TABLE.csv`. If the paper must cite literature, the citations come from these files, not from recall. If a number (an AUROC, a baseline score, a dataset size) is needed, take it from the files or mark it `[CHECK]` — never invent it.

### 2. Build the claim→evidence map before drafting

Write the skeleton as a list of claims, each pointing at its evidence:

```
Claim 1: ViANLI's XLM-R Large reaches only 45.5%  → evidence: VIANLI table (confirm exact figure)
Claim 2: SE's NLI aggregation is the failure point → evidence: ablation table, H1 result
```

A claim with no evidence is either a contribution you have not earned or a sentence to delete. Do not let a claim into prose without an evidence anchor. The reviewer stress test (step 5) will find the ones you missed.

### 3. Draft section by section, in the target's conventions

**Vietnamese academic register.** Formal, impersonal. Prefer active, subject-flexible constructions over English passives. Address conventions follow the faculty: usually avoid "tôi"; use "chúng tôi" (formal paper) or the required impersonal style for the thesis. Keep technical terms in English exactly as the source uses them (per the `vietnamese-translator` skill's core rule), with diacritics correct everywhere.

**English academic register.** Formal, precise, no contractions. Prefer the active voice and short subject-verb-object sentences. Define every acronym at first use.

Common section guidance (adapt to target):

- **Abstract** — problem, method in one line, one headline result with its CI, one sentence of significance. No citations, no undefined acronyms.
- **Introduction** — 3–5 paragraphs: why the problem matters, what is known and its limit, what you do in one sentence, the contributions as a numbered list tied to tables/figures.
- **Related work** — grouped by theme; for each group state the shared limitation *and where you differ*. The difference, not the summary, is the content.
- **Method** — enough detail to reproduce: model, data, hyperparameters, seeds. Reuse the `experiment-runner` conventions (same backbone, budget, seeds).
- **Experiments** — datasets with access status, baselines, the matrix, ablations, metrics with uncertainty, and the cost table. Report raw quality (accuracy) before discrimination (AUROC).
- **Conclusion** — the answer to the RQ, the limits you admit, and one direction forward. Never overclaim here.

### 4. Write the numbers the way a reviewer wants to see them

- Headline results as `mean ± std` over seeds, with a CI and (for comparisons) a paired-test p-value.
- State what was *not* done as clearly as what was. A self-admitted limit reads as rigor, not weakness.
- Do not claim SOTA, a new benchmark, or a contribution that the experiments do not support. Scope the claim to the evidence.

### 5. Reviewer stress test (run it before you finish)

Answer the three hardest questions a reviewer will ask, and fix the draft so the answers are already in the text:

1. "What is new here, precisely — one sentence?"
2. "Which table or figure proves your main claim, and does it actually show that?"
3. "Why is this not just X (the nearest prior work) applied to Y (your data)?"

If the text cannot answer them, the manuscript is not ready.

### 6. Consistency pass, then gate mechanically

- **Terminology glossary.** The same concept gets the same English/Vietnamese term throughout (pick one for `user`/`người dùng`, `hallucination`/`ảo giác`, etc. and hold it).
- **Citations.** Every in-text citation has a reference entry and vice versa. If you introduced citations, run the `citation-auditor` skill on them.
- **Gate the draft:**

```bash
python scripts/check_draft.py --dir ./draft --language vi|en
```

This flags missing required sections, a claim without an evidence anchor, leftover `TODO`/`[CHECK]`/placeholder text, undefined acronyms, and obvious language-register violations (contractions in English; missing diacritics in Vietnamese).

## Output shape

Deliver the manuscript in the target language and the requested format (Markdown by default; convert to LaTeX/Word only if asked). For a thesis, produce the chapter structure the faculty expects, not the paper structure. Include the claim→evidence map as an appendix or a comment block unless the user says otherwise.

## Honest limits

- **No invented numbers.** Every figure comes from the material or is marked `[CHECK]`.
- **No invented citations.** Literature comes from the library or is verified by the `citation-auditor` skill.
- **Style is a floor, not the product.** This skill guarantees structure and support, not acceptance. The experiments are what get a paper accepted.
- **Faculty formats vary.** Theses follow the specific university template; when in doubt, ask for it rather than guessing margins, fonts, or citation style.

## Bundled scripts

| Script | Purpose |
|---|---|
| `scripts/check_draft.py` | Gate a draft: required sections, evidence anchors, no placeholders, acronyms, register |

Takes `--help`; standard library only.
