#!/usr/bin/env python3
"""Acquire the full text of a paper from whatever the user hands over, and say honestly
what was readable. This is the deterministic first step of paper-reader; the critique is
still the agent's job, but "did we actually get the text, or just an abstract?" should
not be re-derived by hand every time.

Input kinds (auto-detected):
  - a local .pdf path            -> pdftotext; detects scanned/image-only PDFs
  - a DOI (10.xxxx/...)          -> Crossref metadata + abstract; notes likely paywall
  - an arXiv id or URL           -> export API abstract + PDF download, then extract
  - a PubMed id (digits) or URL  -> efetch abstract
  - any http(s) URL              -> download; if PDF, extract; else keep as plain text

CLI:
  python fetch_source.py path/to/paper.pdf --out fulltext.txt --meta meta.json
  python fetch_source.py 10.1038/s41597-022-01498-w --out fulltext.txt
  python fetch_source.py https://arxiv.org/abs/2610.22350 --out fulltext.txt
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def get(url, binary=False, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "ignore")


def pdf_to_text(path):
    if not shutil.which("pdftotext"):
        return "", "pdftotext not installed"
    out = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True)
    text = out.stdout
    return text, None


def pdf_pages(path):
    if not shutil.which("pdfinfo"):
        return None
    out = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else None


def detect_scanned(text):
    return len(text.strip()) < 200


def classify_input(inp):
    if os.path.exists(inp):
        return "pdf", inp
    if inp.lower().startswith("http"):
        return "url", inp
    if re.match(r"10\.\d{4,9}/", inp):
        return "doi", inp
    if inp.lower().startswith("arxiv:"):
        return "arxiv", inp[6:].strip()
    if re.match(r"^(?:arxiv\.org/)?(?:abs|pdf)/", inp.lower()):
        return "arxiv", re.search(r"(?:abs|pdf)/([\w.\-]+)", inp).group(1)
    if inp.isdigit():
        return "pubmed", inp
    return "unknown", inp


def handle_pdf(path):
    text, err = pdf_to_text(path)
    pages = pdf_pages(path)
    scanned = detect_scanned(text)
    meta = {"kind": "pdf", "path": path, "pages": pages, "words": len(text.split()),
            "scanned": scanned, "readable": not scanned, "note": err}
    return text, meta


def handle_doi(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi) + "?mailto=paper-reader@example.org"
    msg = get(url)
    msg = json.loads(msg)["message"]
    title = (msg.get("title") or [""])[0]
    abstract = re.sub(r"<[^>]+>", "", msg.get("abstract") or "").strip()
    venue = (msg.get("container-title") or [""])[0]
    year = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
    meta = {"kind": "doi", "doi": doi, "title": title, "venue": venue, "year": year,
            "has_abstract": bool(abstract),
            "note": "Crossref metadata only; full text likely paywalled. Use paper-library "
                    "to fetch an OA copy."}
    body = f"TITLE: {title}\nVENUE: {venue} ({year})\n\nABSTRACT:\n{abstract}"
    return body, meta


def handle_arxiv(aid):
    url = f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(aid)}"
    xml = get(url)
    title = re.search(r"<title>([^<]+)</title>", xml)
    title = title.group(1).strip() if title else aid
    summary = re.search(r"<summary>([^<]+)</summary>", xml)
    summary = re.sub(r"\s+", " ", summary.group(1)).strip() if summary else ""
    pdf_url = f"https://arxiv.org/pdf/{aid}"
    meta = {"kind": "arxiv", "arxiv_id": aid, "title": title, "url": f"https://arxiv.org/abs/{aid}"}
    try:
        blob = get(pdf_url, binary=True)
    except Exception as e:
        meta["note"] = f"PDF download failed ({e}); returning abstract"
        return f"TITLE: {title}\n\nABSTRACT:\n{summary}", meta
    if not blob[:5] == b"%PDF-":
        meta["note"] = "download did not return a PDF; returning abstract"
        return f"TITLE: {title}\n\nABSTRACT:\n{summary}", meta
    tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), f"paper-reader-{aid}.pdf")
    with open(tmp, "wb") as f:
        f.write(blob)
    text, err = pdf_to_text(tmp)
    scanned = detect_scanned(text)
    meta.update(pages=pdf_pages(tmp), words=len(text.split()), scanned=scanned,
                readable=not scanned, note=err)
    os.remove(tmp)
    return text, meta


def handle_pubmed(pid):
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed"
           f"&id={pid}&rettype=abstract&retmode=text")
    text = get(url)
    meta = {"kind": "pubmed", "pmid": pid, "readable": bool(text.strip()),
            "note": "PubMed abstract (full text may be free on PMC — check there)"}
    return text, meta


def handle_url(url):
    try:
        blob = get(url, binary=True)
    except Exception as e:
        return "", {"kind": "url", "url": url, "readable": False, "note": str(e)}
    if blob[:5] == b"%PDF-":
        tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "paper-reader-url.pdf")
        with open(tmp, "wb") as f:
            f.write(blob)
        text, err = pdf_to_text(tmp)
        scanned = detect_scanned(text)
        meta = {"kind": "url", "url": url, "pages": pdf_pages(tmp), "words": len(text.split()),
                "scanned": scanned, "readable": not scanned, "note": err}
        os.remove(tmp)
        return text, meta
    text = blob.decode("utf-8", "ignore")
    return text, {"kind": "url", "url": url, "readable": len(text.strip()) > 0,
                  "note": "returned non-PDF content (HTML/markdown)"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="PDF path, DOI, arXiv id/url, PubMed id, or URL")
    ap.add_argument("--out", help="Write extracted text here")
    ap.add_argument("--meta", help="Write a JSON report of what was readable here")
    args = ap.parse_args()

    kind, val = classify_input(args.input)
    handlers = {"pdf": handle_pdf, "doi": handle_doi, "arxiv": handle_arxiv,
                "pubmed": handle_pubmed, "url": handle_url}
    if kind == "unknown":
        print(f"error: cannot classify input: {args.input}", file=sys.stderr)
        sys.exit(2)

    text, meta = handlers[kind](val)
    meta["input"] = args.input
    meta["characters"] = len(text)

    print(f"kind: {kind}")
    print(f"readable: {meta.get('readable', 'n/a')}")
    for k in ("pages", "words", "characters", "title", "venue", "year", "scanned", "note"):
        if meta.get(k) not in (None, ""):
            print(f"{k}: {meta[k]}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote text ({len(text)} chars) to {args.out}")
    if args.meta:
        with open(args.meta, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        print(f"wrote meta to {args.meta}")


if __name__ == "__main__":
    main()
