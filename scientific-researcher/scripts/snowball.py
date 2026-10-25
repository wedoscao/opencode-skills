#!/usr/bin/env python3
"""Snowball from a seed paper: pull its references and citing papers, then rank by
relevance to a query. Backward (references) surfaces the cluster the seed builds on;
forward (citations) surfaces who is extending it — the two moves that beat keyword
search for finding the relevant cluster of work.

Uses the Semantic Scholar Graph API, which gives references + citations in one call.

CLI:
  python snowball.py --doi 10.1145/3641289 --query "LLM hallucination calibration" \
      --limit 20 --out snowball.json
  python snowball.py --arxiv 2401.12345 --query "..." --out snowball.json
"""
import argparse
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; scientific-researcher/1.0)"
STOP = {"the", "and", "for", "with", "from", "that", "this", "using", "based", "towards",
        "via", "into", "over", "under", "a", "an", "of", "on", "in", "to"}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s)


def tokens(s):
    return {w for w in norm(s).split() if len(w) > 3 and w not in STOP}


def get_json(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def fetch_seed(seed):
    if seed.startswith("10."):
        ident = "DOI:" + urllib.parse.quote(seed)
    elif seed.lower().startswith("arxiv:"):
        ident = "ARXIV:" + seed.split(":", 1)[1]
    else:
        ident = seed  # accept a bare Semantic Scholar paperId too
    fields = ("title,abstract,year,venue,externalIds,"
              "references.title,references.abstract,references.year,references.venue,"
              "references.externalIds,references.openAccessPdf,references.paperId,"
              "citations.title,citations.abstract,citations.year,citations.venue,"
              "citations.externalIds,citations.openAccessPdf,citations.paperId")
    url = f"https://api.semanticscholar.org/graph/v1/paper/{ident}?" + urllib.parse.urlencode({"fields": fields})
    return get_json(url)


def flatten(seed):
    seen, out = set(), []
    for side in ("references", "citations"):
        for p in seed.get(side, []) or []:
            key = p.get("paperId") or p.get("title")
            if not key or key in seen:
                continue
            seen.add(key)
            ext = p.get("externalIds") or {}
            out.append({
                "side": side,
                "title": p.get("title"),
                "year": p.get("year"),
                "venue": p.get("venue"),
                "doi": ext.get("DOI"),
                "arxiv_id": ext.get("ArXiv"),
                "open_access_pdf": (p.get("openAccessPdf") or {}).get("url"),
                "abstract": p.get("abstract"),
            })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doi", help="Seed DOI (10.xxxx/...). Mutually exclusive with --arxiv.")
    ap.add_argument("--arxiv", help="Seed arXiv id (e.g. 2401.12345).")
    ap.add_argument("--query", help="Optional relevance query; without it, order is by year.")
    ap.add_argument("--limit", type=int, default=20, help="Top N after ranking (default 20)")
    ap.add_argument("--out", help="Write JSON here")
    args = ap.parse_args()

    if not args.doi and not args.arxiv:
        print("error: provide --doi or --arxiv", file=sys.stderr)
        sys.exit(2)
    seed_id = args.doi or ("arxiv:" + args.arxiv)

    try:
        seed = fetch_seed(seed_id)
    except Exception as e:
        print(f"error fetching seed {seed_id}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"seed: {seed.get('title')} ({seed.get('year')})")
    papers = flatten(seed)
    refs = sum(1 for p in papers if p["side"] == "references")
    cites = sum(1 for p in papers if p["side"] == "citations")
    print(f"references: {refs} · citations: {cites}")

    if args.query:
        q = tokens(args.query)
        for p in papers:
            t = tokens(p.get("title") or "")
            p["_overlap"] = round(len(t & q) / len(q), 3) if q else 0.0
        papers.sort(key=lambda p: (-p["_overlap"], -(p.get("year") or 0)))
    else:
        papers.sort(key=lambda p: (-(p.get("year") or 0)))

    for p in papers:
        p.pop("_overlap", None)

    print()
    for i, p in enumerate(papers[:args.limit], 1):
        print(f"{i:2d}. [{p['side'][:3]:3s}] {p.get('year') or '----'} | "
              f"{(p.get('venue') or '')[:26]:26s} | {(p.get('title') or '')[:58]}")

    if args.out:
        payload = {"seed": seed_id, "seed_title": seed.get("title"),
                   "references": refs, "citations": cites, "results": papers[:args.limit]}
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        print(f"\nwrote {min(args.limit, len(papers))} to {args.out}")


if __name__ == "__main__":
    main()
