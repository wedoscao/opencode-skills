#!/usr/bin/env python3
"""Search multiple literature sources and merge them into one deduplicated table.

The agent should not hand-build PubMed E-utilities, arXiv, Semantic Scholar and Crossref
URLs every time — nor dedupe results by eye. This does both, and keeps a machine-readable
record of the exact queries and sources used so the final report is reproducible.

Sources:
  pubmed          E-utilities esearch + esummary
  arxiv           export API (Atom), includes abstracts
  semanticscholar Graph API (includes abstracts + OA links)
  crossref        works query

CLI:
  python search_literature.py --query "coffee and cardiovascular disease" \
      --query "coffee all-cause mortality" \
      --sources pubmed,arxiv,semanticscholar,crossref --limit 20 --out results.json
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (compatible; scientific-researcher/1.0; mailto:research@example.org)"
NS = {"a": "http://www.w3.org/2005/Atom", "ar": "http://arxiv.org/schemas/atom"}


def norm_title(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def get_text(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


# --- sources -----------------------------------------------------------------

def pubmed(query, limit):
    out = []
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    es = get_json(f"{base}/esearch.fcgi?db=pubmed&term={urllib.parse.quote(query)}&retmax={limit}&retmode=json")
    ids = es.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return out
    summ = get_json(f"{base}/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json")
    res = summ.get("result", {})
    for pid in res.get("uids", []):
        rec = res.get(pid, {})
        doi = None
        for aid in rec.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value")
        out.append({
            "source": "pubmed",
            "title": rec.get("title", "").rstrip("."),
            "year": _year(rec.get("pubdate") or rec.get("sortpubdate")),
            "venue": rec.get("fulljournalname"),
            "doi": doi,
            "arxiv_id": None,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
            "abstract": None,
            "open_access_pdf": None,
            "authors": [a.get("name") for a in rec.get("authors", [])],
        })
    return out


def arxiv(query, limit):
    out = []
    url = ("http://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(f"all:{query}")
           + f"&max_results={limit}")
    root = ET.fromstring(get_text(url))
    for entry in root.findall("a:entry", NS):
        title = (entry.findtext("a:title", "", NS) or "").strip()
        summary = (entry.findtext("a:summary", "", NS) or "").strip()
        aid = (entry.findtext("a:id", "", NS) or "").strip()
        arxiv_id = aid.rsplit("/abs/", 1)[-1] if "/abs/" in aid else aid
        doi = entry.findtext("ar:doi", "", NS) or None
        out.append({
            "source": "arxiv",
            "title": title,
            "year": _year(entry.findtext("a:published", "", NS)),
            "venue": "arXiv preprint",
            "doi": doi,
            "arxiv_id": arxiv_id,
            "url": aid,
            "abstract": summary,
            "open_access_pdf": f"https://arxiv.org/pdf/{arxiv_id}",
            "authors": [a.findtext("a:name", "", NS) for a in entry.findall("a:author", NS)],
        })
    return out


def semanticscholar(query, limit):
    out = []
    fields = "title,abstract,year,venue,authors,externalIds,openAccessPdf,url"
    url = ("https://api.semanticscholar.org/graph/v1/paper/search?"
           + urllib.parse.urlencode({"query": query, "limit": limit, "fields": fields}))
    data = get_json(url)
    for p in data.get("data", []):
        ext = p.get("externalIds") or {}
        out.append({
            "source": "semanticscholar",
            "title": p.get("title"),
            "year": p.get("year"),
            "venue": p.get("venue"),
            "doi": ext.get("DOI"),
            "arxiv_id": ext.get("ArXiv"),
            "url": p.get("url"),
            "abstract": p.get("abstract"),
            "open_access_pdf": (p.get("openAccessPdf") or {}).get("url"),
            "authors": [a.get("name") for a in p.get("authors", [])],
        })
    return out


def crossref(query, limit, mailto):
    out = []
    params = {"query.bibliographic": query, "rows": str(limit),
              "select": "DOI,title,container-title,issued,type,author"}
    if mailto:
        params["mailto"] = mailto
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = get_json(url)
    for it in data.get("message", {}).get("items", []):
        out.append({
            "source": "crossref",
            "title": (it.get("title") or [""])[0],
            "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
            "venue": (it.get("container-title") or [""])[0] or None,
            "doi": it.get("DOI"),
            "arxiv_id": None,
            "url": f"https://doi.org/{it.get('DOI')}" if it.get("DOI") else None,
            "abstract": None,
            "open_access_pdf": None,
            "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])],
        })
    return out


def _year(date_str):
    m = re.search(r"(19|20)\d{2}", str(date_str or ""))
    return int(m.group(0)) if m else None


# --- merge ---------------------------------------------------------------

def dedupe(records):
    """Prefer records that carry a DOI, then those with an abstract."""
    seen = {}
    for r in records:
        key = (r.get("doi") or "").lower()
        if not key:
            key = "t:" + norm_title(r.get("title") or "")
        if not key.strip(":") or key == "t:":
            continue
        if key not in seen or _better(r, seen[key]):
            seen[key] = r
    return list(seen.values())


def _better(a, b):
    a_score = (1 if a.get("doi") else 0) + (1 if a.get("abstract") else 0)
    b_score = (1 if b.get("doi") else 0) + (1 if b.get("abstract") else 0)
    return a_score > b_score


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", action="append", required=True, help="Search query; repeatable")
    ap.add_argument("--sources", default="pubmed,arxiv,semanticscholar,crossref",
                    help="Comma list: pubmed,arxiv,semanticscholar,crossref")
    ap.add_argument("--limit", type=int, default=20, help="Results per source (default 20)")
    ap.add_argument("--mailto", default=None, help="Crossref polite-pool email")
    ap.add_argument("--out", help="Write merged JSON here")
    args = ap.parse_args()

    srcs = [s.strip() for s in args.sources.split(",") if s.strip()]
    funcs = {"pubmed": pubmed, "arxiv": arxiv, "semanticscholar": semanticscholar, "crossref": crossref}
    unknown = [s for s in srcs if s not in funcs]
    if unknown:
        print(f"error: unknown sources: {unknown}", file=sys.stderr)
        sys.exit(2)

    records = []
    counts = {}
    for q in args.query:
        for s in srcs:
            try:
                got = funcs[s](q, args.limit) if s != "crossref" else funcs[s](q, args.limit, args.mailto)
            except Exception as e:
                print(f"ERR  [{s}] {q[:50]}: {e}", file=sys.stderr)
                continue
            for r in got:
                r["query"] = q
            records.extend(got)
            counts.setdefault(s, 0)
            counts[s] += len(got)
            time.sleep(0.3)

    merged = dedupe(records)
    merged.sort(key=lambda r: (r.get("year") is None, -(r.get("year") or 0)))

    print(f"{len(records)} raw → {len(merged)} unique")
    for s, n in counts.items():
        print(f"  {s}: {n}")
    print()
    for i, r in enumerate(merged[:30], 1):
        print(f"{i:2d}. [{r['source'][:4]:4s}] {r.get('year') or '----'} | "
              f"{(r.get('venue') or '')[:26]:26s} | {r['title'][:58]}")

    if args.out:
        payload = {
            "_meta": {
                "queries": args.query,
                "sources": srcs,
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "raw": len(records),
                "unique": len(merged),
            },
            "results": merged,
        }
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        print(f"\nwrote {len(merged)} records to {args.out}")


if __name__ == "__main__":
    main()
