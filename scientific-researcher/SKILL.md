---
name: scientific-researcher
description: Research a scientific question end-to-end — search for and discover relevant literature, evaluate source quality and evidence strength, and synthesize the findings into a cited summary or literature review. Use when the user explicitly asks to research a scientific topic, find papers/studies/evidence on a question, do a literature search or review, gather the scientific evidence for or against a claim, or understand "what does the research say about X". For reading, summarizing, or critiquing a specific paper the user already has, use the paper-reader skill instead.
---

# Scientific Researcher

Work like a careful researcher gathering and weighing evidence on a question, then report what the literature actually establishes — not just a list of search hits. The goal is a defensible, cited answer to a scientific question, with the strength of the evidence made explicit.

## Before you search

Clarify the question enough to search well, but don't stall on it. When the request is genuinely ambiguous, ask one short question about scope or make a sensible default explicit and proceed.

Nail down three things, stated in your answer:

1. **The question** — restated as a precise, answerable question (population, intervention/exposure, comparison, outcome if it's a clinical-type question).
2. **Scope** — how deep to go (quick answer vs. thorough review), any date range, and whether preprints count.
3. **What you can actually access** — most academic full texts are paywalled. Plan to work largely from abstracts, open-access full texts, and preprint servers, and say so.

## 1. Search and discover literature

Search several sources, not one, because no single database covers everything and each has different coverage and freshness.

**Sources to use (via web search and direct API/HTTP access):**

| Source | What it's good for | Access |
| --- | --- | --- |
| PubMed | Biomedical and life sciences | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<query>&retmax=20` then `efetch`/`esummary` |
| arXiv | Physics, CS, math, quantitative bio | `http://export.arxiv.org/api/query?search_query=<query>&max_results=20` |
| bioRxiv / medRxiv | Preprints in the life sciences | web search / fetch the paper page |
| Semantic Scholar | Broad coverage, citations, open-access links | `https://api.semanticscholar.org/graph/v1/paper/search?query=<query>&fields=title,abstract,year,authors,externalIds,openAccessPdf` |
| Crossref | Finding DOIs and metadata for a known title | `https://api.crossref.org/works?query=<query>&rows=20` |
| Google Scholar | Broadest, includes citations and gray literature | no API — use web search or fetch results pages |
| General web search | Guidelines, registries (ClinicalTrials.gov), systematic review databases (Cochrane) | websearch |

**Prefer the bundled scripts over hand-built URLs.** Query every source, dedupe by DOI/title, and keep the provenance you must report, in one call:

```bash
python scripts/search_literature.py --query "<query 1>" --query "<query 2>" \
  --sources pubmed,arxiv,semanticscholar,crossref --out results.json
```

`results.json` records the exact queries, sources, and timestamp (so the report's "search log" is reproducible), and merges the hits into one de-duplicated table with DOI / year / venue / OA status / abstract. Keep the raw `--query` strings you used so you can report them.

**Build good queries.** Use specific terms, synonyms, and Boolean operators where the source supports them. Start narrow, then broaden. Keep a note of the exact queries and sources you used so you can report them.

**Get coverage, not just recency.** For a credible answer you need, at minimum:

- **Seminal work** — the foundational papers the field is built on.
- **Recent work** — the last few years, to capture current understanding.
- **The strongest evidence** — systematic reviews and meta-analyses first, then primary studies.
- **Opposing or null findings** — actively look for evidence against the headline claim; do not stop at the first confirming results.

**Snowball from the best papers.** Take a high-quality, on-topic paper and look at both its references (backward) and papers that cite it (forward). This reliably surfaces the relevant cluster of work faster than keyword search alone.

```bash
python scripts/snowball.py --doi <seed-doi> --query "<the question>" --out snowball.json
```

It pulls the seed's references and citations from Semantic Scholar in one call and ranks them by overlap with your question, so you read the on-topic neighbours first instead of a flat list.

## 2. Evaluate sources and evidence strength

Do not treat every paper you find as equally trustworthy. Weight sources by how strong their evidence is, and report that weighting.

**Evidence hierarchy (rough, from strongest to weakest):**

1. Systematic reviews and meta-analyses of randomized controlled trials
2. Randomized controlled trials
3. Cohort studies
4. Case-control studies
5. Cross-sectional studies and case series
6. Expert opinion, editorials, narrative reviews
7. Preprints (not yet peer-reviewed)

**But don't apply the hierarchy mechanically.** A well-conducted cohort study can be more informative than a badly-conducted trial. Judge quality within each level:

- **Design** — Is it the right design for the question? Is there a proper comparison/control group?
- **Sample** — Size and statistical power; selection bias; how representative it is.
- **Measurement** — How exposure and outcome were measured; validity and reliability; blinding where relevant.
- **Analysis** — Confounding addressed? Appropriate statistics? Effect sizes and confidence intervals reported, not just p-values? Multiple comparisons handled? Missing data treated?
- **Claims vs. evidence** — Does the paper overclaim? Causal language for correlational findings? Limitations acknowledged?
- **Integrity** — Conflicts of interest, funding source, pre-registration, retraction status, and whether the venue is reputable or a known predatory journal.

**Red flags** to weight against a source: tiny sample, no control group, self-reported or unvalidated outcomes, p-hacking / outcome switching, undeclared conflicts, pay-to-publish venues, retracted or non-reproducible work, and single studies that contradict a large body of evidence.

Prefer **systematic reviews and meta-analyses** as the backbone of your answer; treat individual primary studies as supporting detail. When the literature is sparse, say so rather than inflating the confidence.

## 3. Read the key sources

For the handful of papers that carry the most weight, actually read them — the abstract is the authors' framing and often omits limitations. The `paper-reader` skill has the detailed method for reading and critiquing individual papers; apply it to each key source rather than re-deriving it here. Distinguish three layers throughout: what a paper *says*, what it *shows*, and your *interpretation*.

When full text is paywalled, work from the abstract and say explicitly that you did.

## 4. Synthesize

Don't just report papers one by one. Organize around the question and the themes the literature clusters into:

- **Lead with the answer** to the question, then support it.
- **Group by theme or sub-question**, not by paper.
- **Attribute every claim** to its source (authors, year). Never merge numbers across studies or imply a consensus the papers don't state.
- **Weight the claims** — a conclusion backed by multiple meta-analyses deserves more confidence than one backed by a single small study. Say which claims are well-established, which are suggestive, and which are contested.
- **Note agreement, disagreement, and gaps** — where studies conflict, where they can't be compared (different populations, outcomes, designs), and what is still unknown.
- **Separate findings from interpretation** — keep what the literature shows distinct from what you conclude from it.

## 5. Report

Pick the format the request calls for. Both share citation conventions below.

### Cited summary report

```
# [Research question]

## Executive summary
The direct answer in 2–4 sentences, with the level of confidence stated.

## What the evidence shows
Findings organized by theme or sub-question, each attributed to sources.

## Strength of the evidence
How much confidence is warranted, and why — the best evidence, its quality,
and the main uncertainties.

## Key sources
The most important papers, each with a one-line takeaway.

## Open questions / caveats
What remains uncertain, and what you could not access or verify.
```

### Literature review

```
# [Topic] — Literature review

## Scope and method
Research question, search terms, sources searched, date range, inclusion criteria.

## Background
## [Theme 1]
## [Theme 2]
## ...
## Where the field agrees and disagrees
## Gaps and open questions
## References
```

**Citations.** Use author-year inline — e.g. (Smith et al., 2021) — and a References section with full entries (authors, year, title, venue, DOI or URL) for everything you actually relied on. Prefer DOIs; they are stable and verifiable. Cite only what you actually found and used.

## Rules that always apply

- **Don't fabricate.** Never invent papers, numbers, statistics, or findings. If you couldn't find evidence, say the evidence is absent or sparse — don't fill the gap.
- **Be honest about access.** State what you actually read (abstract vs. full text) and flag anything paywalled or unverifiable. A search that returned nothing is a real result; report it.
- **Report the search.** Include which sources and queries you used, especially for a review. This makes the answer reproducible and shows what was covered.
- **Date everything.** Say when the search was done and the publication dates of key sources, so currency is clear.
- **Flag preprint vs. peer-reviewed.** Treat preprints as tentative; say clearly when a key claim rests on one.
- **Weigh, don't just list.** The value of this skill is judgment about evidence strength, not the number of papers found.
- **Stay on the question.** Resist drifting into adjacent topics; keep the answer scoped to what was asked.
