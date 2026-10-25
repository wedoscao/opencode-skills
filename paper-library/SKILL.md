---
name: paper-library
description: Build a curated, verified PDF library of peer-reviewed papers for one or more research directions, prioritizing Scopus/Web of Science indexed venues. Use this whenever the user asks to find, collect, download, or organize papers/PDFs/literature for a topic, build a reading list or related-work folder, prepare a literature review, or says things like "tải paper về ...", "tìm bài báo cho hướng ...", "gom tài liệu tham khảo", "cho tôi thư viện paper", even when they do not mention Scopus, open access, or PDFs. Also use it when a user complains that downloaded PDFs are paywalled, blocked, wrong files, or badly organized, or when they need papers grouped by research direction with citations and DOIs.
---

# Paper Library

Build a research reading library that the user can trust: correct papers, real metadata, honest labeling of what could and could not be obtained.

The failure mode this skill exists to prevent is the *plausible but wrong* library: a remembered DOI that resolves to a different paper, a 403 HTML page saved as `.pdf`, an arXiv preprint cited as if it were the journal article, or a quartile claimed from memory. Every step below exists because one of those happened.

## Workflow

### 1. Agree on scope before downloading

Establish, in one short exchange:

- The research directions (2-6). If the user gives a broad area, propose a decomposition and confirm rather than guessing.
- Papers per direction (default 6-8). More than ~10 per folder rarely gets read.
- Recency/quality bar: default to landmark + latest, published 2019 or later, surveys capped at ~2 per direction.
- Destination root (default `<cwd>/Papers`) and whether to keep one subfolder per direction.
- Whether the user needs only metadata/DOIs, or actual PDFs.

Ask about language/domain constraints too. A Vietnamese-context library, for example, should prefer datasets and baselines that exist for Vietnamese, not just the most-cited English work.

### 2. Generate candidates, then resolve them properly

Never write a DOI from memory. Resolve every candidate through Crossref and read back the title, container, year:

```bash
python scripts/resolve_candidates.py --query "VinDr-CXR open dataset chest X-rays" \
  --query "temporal knowledge graph completion survey" --out candidates.json
```

The script prints top matches with a similarity score. Anything below ~0.85 is probably a different paper — inspect it. Publisher records sometimes return the medRxiv/SSRN/Research Square preprint instead of the journal version; re-query with the journal name as `--container` to force the published record.

Useful Crossref selectors: `type:journal-article` for journals, `from-pub-date` to enforce recency, `query.container-title` to disambiguate.

### 3. Judge the venue before the paper

Read the returned container name and decide honestly which bucket it is in:

| Bucket | Examples | How to label |
|---|---|---|
| Q1/Q2 journal | Nature, IEEE TMI/TKDE/TPAMI, ACM CSUR/TIST/TOIS, Proc. IEEE, Scientific Data | `Q1`/`Q2` — SCIE/Scopus |
| Solid specialist journal | IEEE Access, MTAP, BMC Medical Imaging, Mathematics, Sensors, Education Sciences | `Q2` — SCIE/Scopus |
| Top conference, Scopus-indexed | CVPR, ICCV, ACL, EMNLP, AAAI, IJCAI, CIKM, MICCAI, ICMR | `Hội nghị A*` / `Hội nghị Scopus` |
| Proceedings that are **not** Scopus journals | NeurIPS, ICLR, MLSys, PMLR-style | label as `Hội nghị (không phải journal)` — do not imply journal indexing |
| Book chapter / edited volume | CRC, Springer LNCS is fine; standalone books vary | `Sách – Scopus tùy` |

Four rules that keep the library honest:

1. **Quartile is an estimate, not a fact.** SJR and JCR reassign quartiles yearly and by category. Write "ước tính" and tell the user to re-check Scopus Sources / JCR before submission. Never state a Q2 as guaranteed.
2. **SCIE/ESCI is not the same as Scopus.** Say which one you mean, or say both only when both are true.
3. **A preprint is not the article.** If the PDF came from arXiv but the paper is published, keep the official DOI and label the file as the preprint of the published version. To tell the two apart, query `export.arxiv.org/api/query?id_list=<id>` and look for `<arxiv:journal_ref>` or `<arxiv:doi>`; if both are absent, search the arXiv title on Crossref and accept a published record only at ≥0.9 title similarity. Quoting an unpublished preprint as if it were peer-reviewed is the single fastest way to lose a reviewer's trust.

   This check is scripted: `python scripts/check_preprint.py --arxiv <id>` (or `--title "<title>"`) reads the arXiv record's `journal_ref`/`doi`, falls back to a Crossref title match at ≥0.9, and prints a verdict (`published` / `preprint-only`) plus the matched record. `fetch_pdfs.py` also marks a `preprint` flag and `oa_status` in its log/manifest, so the final report can state which files are arXiv stand-ins.
4. **Predatory-adjacent venues** (very fast review, high APC, obscure publisher) should be flagged or dropped, not silently included.

### 4. Acquire open-access PDFs with a fallback ladder

Run the ladder in order and stop at the first real PDF. Do not skip step 0.

0. **Unpaywall** (`api.unpaywall.org/v2/<DOI>?email=...`) — try `oa_locations[].url_for_pdf`, then `url`. It is free and needs no key, but often returns landing pages rather than PDFs, so validate the bytes.

   The email must be real. Unpaywall returns an **empty** result list (not an error) for placeholder domains like `example.com`, which looks identical to "this paper has no OA copy". Require `--mailto` or `UNPAYWALL_EMAIL` and refuse to run on a placeholder address.
1. **Publisher OA endpoint** — derive it from the landing page Crossref already gave you (`resource.primary.URL`): MDPI `.../article-slug/pdf`, Springer `link.springer.com/content/pdf/<doi>.pdf`, Nature `/articles/<id>.pdf`, Elsevier `.../pii/<PII>/pdfft`, ACL `aclanthology.org/<id>.pdf`. Deriving beats guessing from the DOI prefix.
2. **arXiv** — search `ti:"<title>"` on the export API and take the matching ID. Use only as a stand-in for a paper that is *also* published; the citation stays the DOI.
3. **Wayback Machine** — `https://web.archive.org/web/2/<publisher-pdf-url>`. This rescues many MDPI/Springer PDFs that Cloudflare blocks, but only if you hand it the **PDF** path, not the article page. Build the PDF path first (step 1), then archive it.

```bash
python scripts/fetch_pdfs.py --plan plan.json --root ~/Documents/Research/Papers
```

`plan.json` is a list of `{"dir": "...", "doi": "...", "note": "why read this"}`.

**Validate bytes, never status codes.** MDPI, Wiley and IEEE return HTTP 200 with a Cloudflare HTML page, and `curl` reports success. A real PDF starts with `%PDF-` and is larger than ~20-30 KB. The script checks both; if you write your own downloader, do the same.

**If urllib fails on Wayback, use curl.** The archive sometimes rejects Python's default request fingerprint; `curl -sL -A "<browser UA>"` works where `urllib` returns HTML.

**Blocked is not the same as paywalled.** Before writing a paper off, check its licence (Unpaywall reports `oa_status`: `gold`, `hybrid`, `green`, `bronze`). Cloudflare on MDPI, Wiley/IET and IEEE frequently fronts an article that is free to read. In one measured run the unassisted path declared a CC BY-ND IET paper "gold OA but blocked — open it in a browser" and stopped, while the same paper came down cleanly through the Wayback step. Giving up on a free paper is the most expensive failure: the user pays for it by hand, one DOI at a time.

### 5. Verify the download actually matches the citation

A library of mislabeled PDFs is worse than no library, because the user will cite the wrong paper.

```bash
python scripts/verify_library.py --root ~/Documents/Research/Papers --log download-log.json
```

It checks: `%PDF` magic, page count, file size, duplicate hashes, and token overlap between the Crossref title and the text extracted from page 1. Investigate every row it flags before reporting success.

To leave the library usable rather than just diagnosed, run it with `--quarantine` (moves bad PDFs and duplicate extras into `root/_quarantine`) and `--update-log` (rewrites the log so those records read `quarantined` instead of `ok`).

Trust page 1 over the DOI. Publisher metadata can be correct while the PDF served at that DOI is a different article: a real case had a Crossref record titled "Vietnamese Spoofing-aware Verification Challenge" whose PDF was a paper on voice conversion. Only the text on page 1 catches that, and only if you compare it to the citation you are about to write.

### 6. Handle the papers you cannot get — do not silently drop them

When a paper is paywalled (typically Springer/Wiley/Elsevier hybrid), choose one of:

- **Replace** it with an open-access paper covering the same role, and say so in the README ("thay cho survey X không OA"). Keep the thematic coverage intact.
- **Keep it in a "need library access" table** with its DOI so the user can pull it through OpenAthens or email the author.

Silently returning 6 papers when the user asked for 8 is a failure; returning 8 with two clearly marked substitutes is a success. Always report the real count.

### 7. Produce documentation the user will actually open

Per direction folder, generate a `README.md` containing the reading path, a table (priority, filename, venue, tier, role, why read), and a citation block with DOIs. At the root, generate `INDEX.md` plus `download-manifest.csv`.

```bash
python scripts/build_docs.py --root ~/Documents/Research/Papers --log download-log.json --meta meta.json
```

`meta.json` maps each DOI to `{priority, role, venue, tier}` — the curation that scripts cannot invent.

Priorities mean "read this first", so use them to encode an argument, not just a ranking: one survey to map the field, one to two method papers for the state of the art, one benchmark/dataset paper to learn how results are measured. A good README tells the user the order in which understanding accumulates.

## Output shape

```
Papers/
├── INDEX.md                  # entry point: directions, counts, reading order, paywalled list
├── download-manifest.csv     # DOI, venue, year, file, source URL, status
├── 01-<direction>/
│   ├── README.md
│   └── <Author>_<Year>_<Short-Title>.pdf
└── 02-<direction>/ ...
```

Filename convention `Author_Year_Slug.pdf` keeps files sortable and greppable, and survives being copied out of the folder. Strip accents and punctuation so shells and links do not break.

## Failure modes and what they look like

| Symptom | Real cause | Fix |
|---|---|---|
| A `.pdf` opens as a Cloudflare/HTML page | MDPI, Wiley, IEEE returned 200 with a challenge page | Check `%PDF-` magic + minimum size, then go to Wayback |
| Unpaywall says "not OA" for a DOI you know is OA | Placeholder email in the request | Use a real address; the API returns empty rather than 403 |
| DOI resolves to a completely different paper | DOI written from memory or from a preprint record | Re-resolve the title via Crossref; prefer the `journal-article` record |
| PDF is the medRxiv/SSRN/Research Square version | Crossref matched the preprint | Re-query with `--container <journal>` or pick the record whose `container-title` is the journal |
| Wayback returns HTML | Archived URL was the article page, not the PDF path | Derive `/pdf`, `content/pdf/<doi>.pdf`, `/pdfft` first |
| A quartile claim contradicts the journal's page | SJR/JCR reassign quartiles yearly and by category | Label as estimate; tell the user to re-check before submission |
| Folder has 6 papers when 8 were requested | Paywalled items were silently dropped | Substitute an OA paper with the same role, or list the DOI under "needs library access" |

## Reporting back

State, in the user's language: how many PDFs per direction, the total, which venues carry the weight (Q1 vs conference), which papers are missing and why, and any substitution you made. Flag the quartile caveat once, briefly, rather than repeating it in every row.

Do not claim a paper is indexed in Scopus/WoS unless the venue genuinely is. If you are unsure, describe the venue and let the user verify.

## Bundled scripts

| Script | Purpose |
|---|---|
| `scripts/resolve_candidates.py` | Titles → verified DOI, venue, year, similarity score (Crossref) |
| `scripts/fetch_pdfs.py` | DOI plan → PDFs via Unpaywall → publisher → arXiv → Wayback, with manifest |
| `scripts/verify_library.py` | Magic bytes, page counts, duplicates, title-vs-page-1 match |
| `scripts/check_preprint.py` | Preprint vs published: arXiv journal_ref/doi + Crossref ≥0.9 title match |
| `scripts/build_docs.py` | Per-folder README + root INDEX + manifest from log and curation |

All scripts take `--help`; none hardcode paths or user identities.
