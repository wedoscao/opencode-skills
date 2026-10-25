"""Verify a reference manifest against Crossref/DataCite/arXiv and local PDFs.

Usage:
    python audit.py --manifest references.csv --out audit-report.md

Manifest CSV columns (header required, order flexible, empty cells allowed):
    key, doi, arxiv, expected_title, expected_first_author, pdf_path

For each row the script checks: identifier resolves and title matches (Crossref,
DataCite fallback), arXiv record title+author match, Anthology-ID-is-not-a-DOI
trap, PDF page-1 title overlap and page count, and the author/et-al. convention.

Standard library only. PDF checks need `pdftotext` and `pdfinfo` on PATH.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ANTHOLOGY_RE = re.compile(r"^10\.18653/", re.IGNORECASE)
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s]+")

UA = "citation-auditor/0.1 (mailto:researcher@example.com)"


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", "replace")


def token_overlap(a: str, b: str) -> float:
    def toks(s):
        return set(re.findall(r"[a-z0-9\u00C0-\u1EF9]+", s.lower()))
    ta, tb = toks(a), toks(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def lookup_doi(doi: str) -> dict | None:
    """Return {title, container, year, authors, source} or None."""
    for source, url in (
        ("crossref", f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"),
        ("datacite", f"https://api.datacite.org/dois/{urllib.parse.quote(doi)}"),
    ):
        try:
            raw = _get(url)
        except Exception as e:  # noqa: BLE001
            print(f"  warn: {source} lookup failed: {e}", file=sys.stderr)
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if source == "crossref":
            msg = data.get("message")
            if not msg:
                continue
            year = None
            for k in ("published-print", "published-online", "published", "issued"):
                if msg.get(k) and msg[k].get("date-parts"):
                    year = msg[k]["date-parts"][0][0]
                    break
            authors = [
                (a.get("family", ""), a.get("given", "")) for a in msg.get("author", [])
            ]
            return {
                "title": (msg.get("title") or [""])[0],
                "container": (msg.get("container-title") or [""])[0],
                "year": year, "authors": authors, "source": "crossref",
            }
        else:
            attrs = data.get("data", {}).get("attributes", {})
            if not attrs.get("titles"):
                continue
            creators = attrs.get("creators", [])
            authors = [(c.get("familyName", ""), c.get("givenName", "")) for c in creators]
            year = attrs.get("publicationYear")
            return {
                "title": attrs["titles"][0].get("title", ""),
                "container": "", "year": year, "authors": authors, "source": "datacite",
            }
    return None


def lookup_arxiv(arxiv_id: str) -> dict | None:
    url = f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}"
    try:
        raw = _get(url)
    except Exception as e:  # noqa: BLE001
        print(f"  warn: arxiv lookup failed: {e}", file=sys.stderr)
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    entry = root.find("a:entry", ns)
    if entry is None:
        return None
    title = (entry.findtext("a:title", "", ns) or "").strip().replace("\n", " ")
    authors = []
    for a in entry.findall("a:author", ns):
        authors.append((a.findtext("a:name", "", ns) or "", ""))
    return {"title": title, "authors": authors, "source": "arxiv"}


def pdf_check(pdf_path: str, expected_title: str) -> dict:
    """Return {pages, title_overlap, opens}. Empty values on missing tools."""
    out = {"pages": None, "title_overlap": None, "opens": False, "note": ""}
    try:
        info = subprocess.run(["pdfinfo", pdf_path], capture_output=True, text=True, timeout=20)
        if info.returncode != 0:
            out["note"] = "pdfinfo failed (not a PDF?)"
            return out
        out["opens"] = True
        m = re.search(r"Pages:\s+(\d+)", info.stdout)
        if m:
            out["pages"] = int(m.group(1))
    except FileNotFoundError:
        out["note"] = "pdfinfo not installed"
        return out
    try:
        txt = subprocess.run(["pdftotext", "-f", "1", "-l", "2", pdf_path, "-"],
                             capture_output=True, text=True, timeout=20).stdout
        if txt.strip():
            out["title_overlap"] = round(token_overlap(expected_title, txt), 3)
    except FileNotFoundError:
        out["note"] = "pdftotext not installed"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", default="audit-report.md")
    ap.add_argument("--title-threshold", type=float, default=0.5,
                    help="min title token-overlap to pass (default 0.5)")
    args = ap.parse_args()

    with open(args.manifest, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    results = []
    for row in rows:
        key = row.get("key", "?")
        doi = (row.get("doi") or "").strip()
        arxiv = (row.get("arxiv") or "").strip()
        exp_title = (row.get("expected_title") or "").strip()
        exp_author = (row.get("expected_first_author") or "").strip()
        pdf = (row.get("pdf_path") or "").strip()

        r = {"key": key, "checks": [], "fix": []}

        # 1. Anthology ID masquerading as DOI
        if ANTHOLOGY_RE.match(doi):
            r["checks"].append(("FAIL", "anthology-id-as-doi",
                                f"'{doi}' is an ACL Anthology ID, not a DOI"))
            r["fix"].append("Cite by Anthology URL (aclanthology.org/...); do not fake a DOI.")

        # 2. DOI resolution
        if doi and not ANTHOLOGY_RE.match(doi):
            rec = lookup_doi(doi)
            if rec is None:
                r["checks"].append(("FAIL", "doi-unresolved", f"DOI {doi} did not resolve"))
                r["fix"].append("Re-query by title on Crossref; correct or drop the DOI.")
            else:
                overlap = token_overlap(exp_title, rec["title"]) if exp_title else 1.0
                status = "PASS" if overlap >= args.title_threshold else "FAIL"
                r["checks"].append((status, "doi-title-match",
                                    f"resolved '{rec['title'][:80]}' (overlap {overlap:.2f}) via {rec['source']}"))
                if status == "FAIL":
                    r["fix"].append("DOI resolves to a different paper; re-resolve the title.")
                if exp_author and rec["authors"]:
                    first_fam = (rec["authors"][0][0] or "").lower()
                    if first_fam and exp_author.lower() not in first_fam and first_fam not in exp_author.lower():
                        r["checks"].append(("FAIL", "first-author-mismatch",
                                            f"expected first author '{exp_author}', resolved '{rec['authors'][0][0]}'"))
                        r["fix"].append("Fix the first author surname.")
                n_auth = len([a for a in rec["authors"] if a[0] or a[1]])
                if n_auth == 2:
                    r["checks"].append(("WARN", "two-author-et-al",
                                        "2 authors: must cite both surnames, not 'et al.'"))
                elif n_auth >= 3:
                    r["checks"].append(("PASS", "et-al-ok", f"{n_auth} authors: 'et al.' allowed"))

        # 3. arXiv resolution
        if arxiv:
            rec = lookup_arxiv(arxiv)
            if rec is None:
                r["checks"].append(("FAIL", "arxiv-unresolved", f"arXiv {arxiv} not found"))
                r["fix"].append("Check the arXiv ID.")
            else:
                overlap = token_overlap(exp_title, rec["title"]) if exp_title else 1.0
                status = "PASS" if overlap >= args.title_threshold else "FAIL"
                r["checks"].append((status, "arxiv-title-match",
                                    f"resolved '{rec['title'][:80]}' (overlap {overlap:.2f})"))
                if status == "FAIL":
                    r["fix"].append("arXiv ID points to a different paper.")
                if exp_author and rec["authors"] and rec["authors"][0][0]:
                    if exp_author.lower() not in rec["authors"][0][0].lower():
                        r["checks"].append(("FAIL", "arxiv-author-mismatch",
                                            f"expected '{exp_author}', arXiv '{rec['authors'][0][0]}'"))
                        r["fix"].append("Fix the first author surname.")

        # 4. PDF page-1 verification
        if pdf:
            p = pdf_check(pdf, exp_title)
            if not p["opens"] and not p["note"].startswith("pdfinfo not installed"):
                r["checks"].append(("FAIL", "pdf-not-openable", p["note"] or "PDF does not open"))
                r["fix"].append("Re-download the PDF.")
            else:
                if p["title_overlap"] is None:
                    r["checks"].append(("WARN", "pdf-skip", p["note"] or "could not extract text"))
                elif p["title_overlap"] >= args.title_threshold:
                    r["checks"].append(("PASS", "pdf-title-match",
                                        f"page-1 overlap {p['title_overlap']:.2f}"))
                else:
                    r["checks"].append(("FAIL", "pdf-title-mismatch",
                                        f"page-1 overlap {p['title_overlap']:.2f} below threshold"))
                    r["fix"].append("Trust page 1 over the DOI; re-download the correct PDF.")

        if not r["checks"]:
            r["checks"].append(("WARN", "nothing-to-check", "no identifier or PDF supplied"))
        results.append(r)

    # Report
    n_fail = sum(1 for r in results for c in r["checks"] if c[0] == "FAIL")
    n_warn = sum(1 for r in results for c in r["checks"] if c[0] == "WARN")
    lines = ["# Citation audit", "",
             f"**{len(results)} references · {n_fail} failed · {n_warn} warnings**", ""]
    for r in results:
        lines.append(f"## {r['key']}")
        for status, code, msg in r["checks"]:
            lines.append(f"- [{status}] `{code}`: {msg}")
        for f in r["fix"]:
            lines.append(f"  - fix → {f}")
        lines.append("")
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"wrote {args.out}: {len(results)} refs, {n_fail} failed, {n_warn} warnings")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
