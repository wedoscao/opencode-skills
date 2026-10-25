#!/usr/bin/env python3
"""Resolve paper titles to verified DOIs/venues via Crossref.

Why this exists: DOIs written from memory are wrong often enough to poison a
library. Crossref gives the canonical title, container and year, plus a
similarity score so a bad match is visible instead of silent.

Example:
  python resolve_candidates.py --query "VinDr-CXR open dataset" \
      --query "Temporal Knowledge Graph Completion survey" --out candidates.json
"""
import argparse
import difflib
import json
import sys
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def resolve(query, rows=5, container=None, from_year=None, mailto=None, timeout=30):
    params = {
        "query.bibliographic": query,
        "rows": str(rows),
        "select": "DOI,title,container-title,issued,type,is-referenced-by-count,author",
    }
    if container:
        params["query.container-title"] = container
    filters = ["type:journal-article"] if container else []
    if from_year:
        filters.append(f"from-pub-date:{from_year}-01-01")
    if filters:
        params["filter"] = ",".join(filters)
    if mailto:
        params["mailto"] = mailto
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    items = get_json(url, timeout)["message"]["items"]

    scored = []
    for it in items:
        title = (it.get("title") or [""])[0]
        score = difflib.SequenceMatcher(None, title.lower(), query.lower()).ratio()
        scored.append((score, {
            "query": query,
            "score": round(score, 2),
            "title": title,
            "doi": it.get("DOI"),
            "venue": (it.get("container-title") or [""])[0],
            "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
            "type": it.get("type"),
            "cites": it.get("is-referenced-by-count"),
            "author": ((it.get("author") or [{}])[0].get("family") or "Anon"),
        }))
    scored.sort(key=lambda x: -x[0])
    return [rec for _, rec in scored]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", action="append", required=True, help="Paper title or descriptive query; repeatable")
    ap.add_argument("--container", help="Journal name hint; also restricts results to journal articles")
    ap.add_argument("--from-year", type=int, help="Drop anything published before this year")
    ap.add_argument("--rows", type=int, default=5, help="Candidates to inspect per query (default 5)")
    ap.add_argument("--mailto", default=None, help="Contact email for Crossref's polite pool (optional)")
    ap.add_argument("--out", help="Write JSON results here")
    args = ap.parse_args()

    results = []
    for q in args.query:
        try:
            hits = resolve(q, args.rows, args.container, args.from_year, args.mailto)
        except Exception as e:  # network hiccups should not kill a batch
            print(f"ERR  {q[:60]}: {e}", file=sys.stderr)
            continue
        if not hits:
            print(f"NONE {q[:60]}", file=sys.stderr)
            continue
        print(f"\n## {q}")
        for i, rec in enumerate(hits[:3]):
            flag = "  <-- check this match" if rec["score"] < 0.85 else ""
            mark = "*" if i == 0 else " "
            print(f"{mark}{rec['score']:.2f} | {rec['year']} | {rec['venue'][:42]:42s} | "
                  f"{rec['doi']} | {rec['title'][:60]}{flag}")
        results.extend(hits)
        time.sleep(0.25)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1)
        print(f"\nwrote {len(results)} records to {args.out}")


if __name__ == "__main__":
    main()
