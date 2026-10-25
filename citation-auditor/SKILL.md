---
name: citation-auditor
description: Verify that every citation is real and correctly formatted — check DOIs against Crossref/DataCite, arXiv IDs against the arXiv API, PDF page-1 title matches, and enforce author-count conventions (et al. only for 3+ authors). Use whenever the user wants to check or audit references, "kiểm tra trích dẫn", "kiểm chứng citation", "soát tài liệu tham khảo", confirm a paper actually exists, or clean a bibliography before submitting.
---

# Citation Auditor

Make every citation provably real before it goes into a paper, thesis, or CV.

The failure mode this skill prevents is the *plausible but wrong reference*: a DOI that resolves to a different paper, a remembered arXiv ID that is someone else's work, a preprint cited as the journal article, an ACL Anthology ID pasted where a DOI belongs, or an "et al." that hides an incorrect first author. Every step exists because one of those happened in practice.

## What to verify (and why it matters)

1. **Existence.** The identifier (DOI, arXiv ID, or URL) returns a real record whose title matches what you are citing. A hallucinated citation is worse than a missing one.
2. **Title match.** The page-1 text of the PDF matches the citation, not just the metadata. Publisher metadata can be correct while the served PDF is a different article.
3. **Author names.** First author is who you wrote. "et al." appears only for 3+ authors; for exactly 2 authors write both surnames.
4. **Venue honesty.** A preprint is not the article. If the PDF is the arXiv version of a published paper, cite the published DOI and label the file as a preprint.
5. **No fake DOIs.** ACL Anthology IDs (`2022.coling-1.339`) look like DOIs but are not. `10.18653/v1/2022.coling-1.339` returns 404 on Crossref. Cite them by Anthology URL.

## Workflow

### 1. Collect the references

Gather what you are citing into a manifest. The audit script reads a CSV with one row per reference. If you already have a `download-manifest.csv` (from the `paper-library` skill) or a references section, adapt it to this schema:

```csv
key,doi,arxiv,expected_title,expected_first_author,pdf_path
farquhar2024,10.1038/s41586-024-07921-5,,Detecting hallucinations in large language models using semantic entropy,Farquhar,/path/farquhar2024.pdf
vinli,,,,Nguyen,/path/vinli.pdf
```

Leave a column empty when it does not apply. For a paper with only an Anthology ID, put the Anthology URL in the `doi` column and it will be flagged as "Anthology, no DOI — cite by URL".

### 2. Run the audit

```bash
python scripts/audit.py --manifest references.csv --out audit-report.md
```

For each row the script:
- **DOI present** → query Crossref (`api.crossref.org/works/<doi>`), fall back to DataCite (`api.datacite.org/dois/<doi>`); report title, container, year; compare the title to `expected_title` with token-overlap similarity.
- **arXiv ID present** → query the arXiv export API; compare title + first author.
- **Anthology-style DOI** (`10.18653/v1/...`) → flag it, because it is an ID, not a DOI.
- **PDF present** → run `pdftotext` on pages 1–2 and compare against `expected_title`; run `pdfinfo` to confirm it opens and has a sane page count.
- **Author convention** → check the "et al." rule against the resolved author list (or `expected_first_author` when the record is unavailable).

The output is a pass/fail table plus a summary: total, verified, failed, and a `fix` column telling the user exactly what to change.

### 3. Fix what the audit found, then re-run

Every failure gets a concrete fix (wrong DOI → the correct one from the lookup; missing DOI → "cite by URL"; "et al." misuse → write both surnames). Apply fixes to the source document, not just the manifest, then re-run to confirm green.

## The rules the script cannot check — check them yourself

- **Quartile/indexing claims** (Q1, Scopus, WoS) are not verifiable from Crossref alone; they change yearly and by category. Never write a quartile into a citation without checking Scopus Sources / JCR directly.
- **"Cited as the journal article but the PDF is a preprint."** The script reports whether the arXiv record has a `journal_ref`/`doi`; use that, plus a title search on Crossref, to decide whether to cite the published version.
- **Semantic correctness.** The script proves the reference exists and matches its title; it does not prove the claim you attached to it. A real paper can still be cited for a claim it never makes. Read the abstract (or more) for every citation you lean on.

## Failure modes and what they look like

| Symptom | Real cause | Fix |
|---|---|---|
| DOI resolves to a different paper | DOI written from memory / from a preprint record | Re-resolve the title via Crossref; pick the `journal-article` record |
| `10.18653/v1/...` returns 404 | It is an Anthology ID, not a DOI | Cite by Anthology URL; don't fake a DOI |
| Crossref title ≠ PDF page-1 title | Metadata is right, the served PDF is a different article | Trust page 1; re-download the correct PDF |
| "et al." hides a wrong first author | First author was guessed | Look up the resolved author list; fix the surname |
| 2 authors written as "X et al." | Convention violation | Write both surnames; "et al." only for 3+ |
| Cited as published but only a preprint exists | arXiv stand-in | Label preprint; cite the published DOI only when verified |

## Reporting back

State, in the user's language: how many references total, how many verified clean, how many failed and why, and the exact edits to make. Highlight the "fake DOI" trap (Anthology IDs) and the quartile caveat once each — don't repeat per row.

## Bundled scripts

| Script | Purpose |
|---|---|
| `scripts/audit.py` | Manifest CSV → verified-by-Crossref/DataCite/arXiv/PDF pass-fail report |

Takes `--help`; uses only the standard library (`urllib`, `json`, `xml.etree`) so it runs anywhere. PDF checks require `pdftotext` and `pdfinfo` on PATH.
