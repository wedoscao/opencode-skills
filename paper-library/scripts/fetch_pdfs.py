#!/usr/bin/env python3
"""Download open-access PDFs for a list of DOIs, with a validated fallback ladder.

Order: Unpaywall -> publisher OA endpoint -> arXiv -> Wayback Machine.
Every candidate is accepted only if the bytes start with %PDF- and exceed
MIN_BYTES, because MDPI/Wiley/IEEE answer 403/200 with an HTML challenge page
and a naive downloader will happily save it as .pdf.

Plan format (JSON list):
  [{"dir": "01-topic", "doi": "10.1234/abc", "note": "why read this"}]

Outputs: PDFs under --root/<dir>/, a log JSON, and a CSV manifest.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
MIN_BYTES = 20_000

PUBLISHER_PDF = [
    ("10.1038/", lambda doi: f"https://www.nature.com/articles/{doi.split('/', 1)[1]}.pdf"),
    ("10.1186/", lambda doi: f"https://link.springer.com/content/pdf/{doi}.pdf"),
    ("10.1007/", lambda doi: f"https://link.springer.com/content/pdf/{doi}.pdf"),
    ("10.3390/", lambda doi: None),  # needs the article URL from Crossref; see derive_pdf_urls
]


def derive_pdf_urls(landing):
    """Publishers expose PDFs at predictable paths; derive them from the landing page."""
    if not landing:
        return []
    urls = []
    host = urllib.parse.urlsplit(landing).netloc.lower()
    path = urllib.parse.urlsplit(landing).path.rstrip("/")
    if "mdpi.com" in host and not path.endswith("/pdf"):
        urls.append(landing.rstrip("/") + "/pdf")
    elif "link.springer.com/article/" in landing:
        urls.append(landing.replace("/article/", "/content/pdf/") + ".pdf")
    elif host.endswith("nature.com") and "/articles/" in path:
        urls.append(landing.rstrip("/") + ".pdf")
    elif "sciencedirect.com/science/article/pii/" in landing:
        urls.append(landing.rstrip("/").split("?")[0] + "/pdfft")
    urls.append(landing)
    return list(dict.fromkeys(urls))


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_json(url, timeout=30):
    return json.loads(fetch(url, timeout).decode("utf-8", "ignore"))


def looks_like_pdf(blob):
    return blob[:5] == b"%PDF-" and len(blob) >= MIN_BYTES


def slug(text, limit=55):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")[:limit].strip("-")


def safe_name(author, year, title):
    name = f"{author}_{year}_{slug(title)}.pdf"
    return re.sub(r"[/\\:*?\"<>|]", "", name)


def crossref(doi, mailto):
    return get_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto={mailto}")["message"]


def unpaywall_pdfs(doi, mailto):
    try:
        data = get_json(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={mailto}")
    except Exception:
        return []
    urls = []
    for loc in data.get("oa_locations") or []:
        for key in ("url_for_pdf", "url"):
            if loc.get(key):
                urls.append(loc[key])
    return list(dict.fromkeys(urls))


def arxiv_pdf(title):
    for query in (f'ti:"{title}"', f'all:"{title}"'):
        try:
            xml = fetch("http://export.arxiv.org/api/query?search_query="
                        + urllib.parse.quote(query) + "&max_results=4", 30).decode("utf-8", "ignore")
        except Exception:
            continue
        for aid in re.findall(r"<id>http://arxiv.org/abs/([^<]+)</id>", xml):
            url = f"https://arxiv.org/pdf/{aid}"
            try:
                blob = fetch(url, 60)
                if looks_like_pdf(blob):
                    return blob, url
            except Exception:
                continue
    return None, None


def wayback_pdf(url):
    """The archive rejects urllib's fingerprint on some hosts; curl works."""
    archive = "https://web.archive.org/web/2/" + url
    try:
        out = subprocess.run(
            ["curl", "-sL", "-m", "70", "-A", UA, archive],
            capture_output=True, timeout=90,
        )
        if looks_like_pdf(out.stdout):
            return out.stdout, archive
    except Exception:
        pass
    return None, None


def acquire(doi, title, mailto, landing=None):
    oa_urls = derive_pdf_urls(landing) + unpaywall_pdfs(doi, mailto)

    for url in oa_urls:
        try:
            blob = fetch(url)
            if looks_like_pdf(blob):
                return blob, url
        except Exception:
            continue

    publisher_url = None
    for prefix, build in PUBLISHER_PDF:
        if doi.startswith(prefix):
            publisher_url = build(doi)
            if publisher_url:
                try:
                    blob = fetch(publisher_url)
                    if looks_like_pdf(blob):
                        return blob, publisher_url
                except Exception:
                    pass
            break

    blob, url = arxiv_pdf(title)
    if blob:
        return blob, url

    # Wayback rescues publishers that answer Cloudflare challenges (MDPI, Springer, Wiley).
    for url in ([publisher_url] if publisher_url else []) + oa_urls:
        blob, src = wayback_pdf(url)
        if blob:
            return blob, src
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, help="JSON list of {dir, doi, note}")
    ap.add_argument("--root", required=True, help="Library root; one subfolder per direction")
    ap.add_argument("--mailto", default=None,
                    help="A real contact email. Unpaywall silently returns zero results for "
                         "placeholder domains such as example.com. Falls back to $UNPAYWALL_EMAIL.")
    ap.add_argument("--log", help="Where to write the JSON log (default <root>/download-log.json)")
    ap.add_argument("--manifest", help="Where to write the CSV manifest (default <root>/download-manifest.csv)")
    args = ap.parse_args()

    mailto = args.mailto or os.environ.get("UNPAYWALL_EMAIL") or os.environ.get("CROSSREF_MAILTO")
    if not mailto or mailto.endswith(("example.com", "example.org")):
        raise SystemExit(
            "A real email is required: Unpaywall returns no results for placeholder addresses.\n"
            "Re-run with --mailto you@university.edu or set UNPAYWALL_EMAIL."
        )
    args.mailto = mailto

    plan = json.load(open(args.plan, encoding="utf-8"))
    log_path = args.log or os.path.join(args.root, "download-log.json")
    manifest_path = args.manifest or os.path.join(args.root, "download-manifest.csv")

    existing = []
    if os.path.exists(log_path):
        try:
            existing = json.load(open(log_path, encoding="utf-8"))
        except Exception:
            existing = []
    done = {r["doi"] for r in existing if r.get("status") == "ok"}

    records = existing
    for item in plan:
        doi = item["doi"]
        if doi in done:
            print(f"skip {doi} (already downloaded)")
            continue
        rec = {"dir": item.get("dir", "papers"), "doi": doi, "note": item.get("note", ""),
               "status": "failed", "file": None, "src": None, "meta": None}
        try:
            cr = crossref(doi, args.mailto)
            landing = ((cr.get("resource") or {}).get("primary") or {}).get("URL")
            meta = {
                "title": (cr.get("title") or [""])[0],
                "venue": (cr.get("container-title") or [""])[0],
                "year": (cr.get("issued", {}).get("date-parts") or [[None]])[0][0],
                "author": ((cr.get("author") or [{}])[0].get("family") or "Anon"),
            }
            rec["meta"] = meta
            blob, src = acquire(doi, meta["title"], args.mailto, landing)
            if blob:
                outdir = os.path.join(args.root, rec["dir"])
                os.makedirs(outdir, exist_ok=True)
                path = os.path.join(outdir, safe_name(meta["author"], meta["year"], meta["title"]))
                with open(path, "wb") as f:
                    f.write(blob)
                rec.update(status="ok", file=os.path.relpath(path, args.root), src=src)
            else:
                rec.update(status="paywalled")
        except Exception as e:
            rec["error"] = str(e)[:160]
        records.append(rec)
        print(f"{rec['status']:10s} {doi}  {(rec['meta'] or {}).get('title', '?')[:58]}  {rec.get('src') or rec.get('error', '')}")
        time.sleep(0.4)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)

    with open(manifest_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Folder", "DOI", "Title", "Venue", "Year", "PDF", "Source URL", "Status"])
        for r in records:
            m = r.get("meta") or {}
            w.writerow([r.get("dir", ""), r["doi"], m.get("title", ""), m.get("venue", ""),
                        m.get("year", ""), r.get("file") or "", r.get("src") or "",
                        "OK" if r["status"] == "ok" else "needs library access"])

    ok = sum(1 for r in records if r["status"] == "ok")
    missing = [r for r in records if r["status"] != "ok"]
    print(f"\nOK {ok}/{len(records)}")
    if missing:
        print("Missing PDFs (use OpenAthens / ask the authors):")
        for r in missing:
            print(f"  {r['doi']}  {(r.get('meta') or {}).get('title', '')[:70]}")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
