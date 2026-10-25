---
name: paper-reader
description: Read, summarize, critique, and extract structured information from scientific papers, and explain them in plain language. Use whenever the user gives you a paper or study to read or understand — as a PDF file, an arXiv/DOI/PubMed/bioRxiv link, or pasted text — or asks for a summary, a critical evaluation of a study, the methods/results/limitations pulled out, a comparison of multiple studies, or a plain-language explanation of research. Trigger even when the user doesn't say "paper" or "study" (e.g. "what does this actually show?", "is this finding legit?", "summarize this article", "explain this like I'm not a scientist", "how strong is this evidence?"). This is for reading and understanding existing papers — not for writing a paper or for searching for literature on a topic (use the scientific-researcher skill for that).
---

# Paper Reader

Read scientific papers the way a careful, skeptical researcher would: understand what the authors did, what they actually found, and how strong the evidence is — then communicate it at whatever depth and level of expertise the reader needs.

> **Finding papers vs. reading them.** This skill reads and critiques papers the user already has. If the user wants to *find* literature on a topic, search for evidence, or answer a question with the body of research, use the `scientific-researcher` skill instead.

## Get the full text first

The abstract alone is not enough for a critique or an extraction — it is the authors' own framing and often omits limitations. Try to read the whole paper before evaluating it.

Start your answer by stating what you actually read and what you couldn't — for example "based on the abstract only" or "based on the full text."

**Use the bundled script to acquire the text** rather than re-deriving the access logic by hand:

```bash
python scripts/fetch_source.py <pdf-path | DOI | arXiv-id | PubMed-id | URL> \
  --out fulltext.txt --meta meta.json
```

It extracts the text and reports honestly what was readable — page count, whether a PDF is scanned/image-only (no text layer), or whether only an abstract was available for a paywalled DOI. Critique from `fulltext.txt`, and state your access level from `meta.json` (the "what I read vs. couldn't" line the skill requires).

- **PDF file**: extract the text (e.g. `pdftotext`, or a PDF-reading capability). Note explicitly when figures, tables, or equations could not be read, since those often hold the real results. If the PDF is a scanned/image-only document and no text comes out, say so — do not guess at content you cannot read; suggest OCR or ask for an accessible version.
- **Link / DOI**:
  - arXiv: `https://arxiv.org/abs/<id>` → fetch the abstract page or `https://arxiv.org/pdf/<id>` for full text.
  - DOI: resolve `https://doi.org/<doi>`. If paywalled, work from the abstract and say the full text was not accessible.
  - PubMed/PMC: the PMC full text is usually freely readable and is the best source.
- **Pasted text / abstract**: work with what you have, and flag that the analysis rests on a partial source.
- **Multiple papers**: read each one, then compare. Keep straight which claim came from which paper.

When full text is unavailable, say so, and keep "the abstract claims X" distinct from "the paper shows X."

## Four modes

The user may want one or several of these. If they don't specify, summarize first and offer the others. Match depth to the request; don't pad a short answer into a long one.

### 1. Summarize

Scale to what was asked:

- **One paragraph**: the question, the approach, the headline finding, and the main caveat.
- **Structured summary**: background/motivation, methods, results, discussion/limitations, mirroring the paper's sections.
- **Deep dive**: add interpretation of figures and tables, key numbers, and how the work fits prior research.

Always state the research question explicitly and lead with the answer.

### 2. Critique / evaluate

Judge the study's validity and the strength of its claims. Work through these layers, spending effort where it matters most:

1. **Question & design** — Is the research question clear? Is the design appropriate (RCT, cohort, case-control, cross-sectional, etc.)? Does the design support the conclusions?
2. **Sample & measurement** — Sample size and statistical power, selection bias, representativeness, how exposure and outcome were measured, and the validity/reliability of those measures.
3. **Confounding & analysis** — Were confounders addressed? Are the statistical methods appropriate? Multiple comparisons handled? Effect sizes reported, not just p-values? How was missing data treated?
4. **Claims vs. evidence** — Does the paper overclaim? Is causal language used for correlational findings? Are the stated limitations complete?
5. **Validity & generality** — Internal validity, external validity/generalizability, and whether the result would plausibly replicate.
6. **Context & integrity** — Conflicts of interest, funding source, pre-registration, and how the paper sits relative to the field.

Report what actually matters. Do not manufacture criticisms to look thorough, and do not be credulous: a study can be well-executed and still support only a modest claim. State clearly what the paper *does* and *does not* establish.

### 3. Extract structured information

Pull out the following fields into a consistent structure, skipping any that don't apply:

- Citation (authors, year, title, venue/DOI)
- Research question / hypothesis
- Study design & setting
- Population / sample (size and characteristics)
- Methods & measurements
- Key results (with numbers, effect sizes, confidence intervals)
- Limitations (acknowledged and apparent)
- Funding / conflicts of interest

For the citation, give authors (year) for in-text reference plus a full reference line (authors, year, title, venue, DOI) when the source provides it. Use a table when comparing multiple papers. Quote exact numbers rather than rounding away precision, and note when a value is not reported.

### 4. Explain to a non-expert

Translate the paper into plain language:

- Replace jargon with everyday terms; define any technical word you must keep, on first use.
- Use concrete analogies, and explain the *why* and *why it matters*, not just the *what*.
- State the key takeaway in one sentence a layperson could repeat to someone else.
- Be honest about uncertainty: "this suggests" rather than "this proves."

## Comparing multiple papers

When asked to compare papers, or for a literature-review style answer, read each one first, then synthesize — don't just summarize each in isolation:

- Lead with the shared research question or theme the papers have in common.
- Use a table: rows are papers, columns are the key dimensions (design, population, key result, effect size, limitations, quality).
- Attribute every claim to its paper. Never merge numbers across studies or imply a consensus the papers don't state.
- Note where papers agree, conflict, or cannot be compared directly (different outcomes, populations, or designs).

## Rules that always apply

- **Don't fabricate.** Never invent numbers, statistics, or findings. If a value isn't in the source, say it isn't reported.
- **Attribute claims.** Say where a claim comes from (which section, figure, or table) so the reader can verify it.
- **Separate three layers:** what the paper *says*, what it *shows*, and your *interpretation*. Don't blur them.
- **Flag confidence.** Note when you're inferring rather than reporting, and when a claim rests on the weak part of the study.
- **Be honest about access.** State up front what you read (abstract only, full text, PDF with or without figures/tables) and flag anything you couldn't access. If a figure, table, or section wasn't readable, say so rather than guessing.

## Report structure

Adapt to the request. For a full analysis, this ordering works well:

```
# [Title]
## Research question
## Summary
## Methods (brief)
## Key findings
## Critical assessment
## Limitations
## Bottom line
```

For a critique-only request:

```
# [Title] — Critical review
## Claim being made
## What the study shows
## Strengths
## Weaknesses / threats to validity
## Verdict
```
