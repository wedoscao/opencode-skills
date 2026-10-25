#!/usr/bin/env python3
"""Tell whether a paper has a published (journal/proceedings) version, or is only a preprint.

This encodes the skill's rule 3.3 mechanically: if the PDF came from arXiv, read the
arXiv record's journal_ref / doi; if neither is present, search the title on Crossref and
accept a published record only at >=0.9 title similarity. A preprint that is *also*
published must keep the official DOI and be labelled as the preprint of that article —
quoting an unpublished preprint as peer-reviewed is the fastest way to lose a reviewer's
trust.

CLI:
  python check_preprint.py --arxiv 2610.22350 [--mailto you@uni.edu]
  python check_preprint.py --title "Vietnamese spoofing-aware verification" [--mailto you@uni.edu]
"""
import argparse
import difflib
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (compatible; paper-library/1.0)"
NS = {"a": "http://www.w3.org/2005/Atom", "ar": "http://arxiv.org/schemas/atom"}
PUBLISHED_TYPES = {"journal-article", "proceedings-article", "book-chapter"}


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def get_text(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def arxiv_record(aid):
    xml = get_text(f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(aid)}")
    root = ET.fromstring(xml)
    entry = root.find("a:entry", NS)
    if entry is None:
        return None
    return {
        "title": (entry.findtext("a:title", "", NS) or "").strip(),
        "journal_ref": (entry.findtext("ar:journal_ref", "", NS) or "").strip() or None,
        "doi": (entry.findtext("ar:doi", "", NS) or "").strip() or None,
    }


def crossref_by_title(title, mailto):
    params = {"query.bibliographic": title, "rows": "5",
              "select": "DOI,title,container-title,issued,type"}
    if mailto:
        params["mailto"] = mailto
    data = get_json("https://api.crossref.org/works?" + urllib.parse.urlencode(params))
    out = []
    for it in data.get("message", {}).get("items", []):
        if it.get("type") not in PUBLISHED_TYPES:
            continue
        t = (it.get("title") or [""])[0]
        score = difflib.SequenceMatcher(None, t.lower(), title.lower()).ratio()
        out.append({
            "score": round(score, 2),
            "title": t,
            "doi": it.get("DOI"),
            "venue": (it.get("container-title") or [""])[0],
            "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
        })
    out.sort(key=lambda r: -r["score"])
    return out


def verdict_for_arxiv(aid, mailto):
    rec = arxiv_record(aid)
    if not rec:
        return {"arxiv_id": aid, "status": "unknown", "note": "could not read arXiv record"}
    if rec["journal_ref"]:
        return {"arxiv_id": aid, "title": rec["title"], "status": "published",
                "journal_ref": rec["journal_ref"], "note": "arXiv record carries a journal_ref"}
    if rec["doi"]:
        return {"arxiv_id": aid, "title": rec["title"], "status": "published",
                "doi": rec["doi"], "note": "arXiv record carries a DOI (published version)"}
    matches = crossref_by_title(rec["title"], mailto)
    if matches and matches[0]["score"] >= 0.9:
        return {"arxiv_id": aid, "title": rec["title"], "status": "published",
                "match": matches[0], "note": f"Crossref title match {matches[0]['score']}"}
    return {"arxiv_id": aid, "title": rec["title"], "status": "preprint-only",
            "best_match": matches[0] if matches else None,
            "note": "no journal_ref/doi and no >=0.9 Crossref match"}


def verdict_for_title(title, mailto):
    matches = crossref_by_title(title, mailto)
    if matches and matches[0]["score"] >= 0.9:
        return {"title": title, "status": "published", "match": matches[0]}
    return {"title": title, "status": "preprint-only",
            "best_match": matches[0] if matches else None,
            "note": "no >=0.9 Crossref match to a published record"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arxiv", help="arXiv id (e.g. 2610.22350)")
    ap.add_argument("--title", help="Preprint title to check against Crossref")
    ap.add_argument("--mailto", help="Crossref polite-pool email")
    args = ap.parse_args()

    if not args.arxiv and not args.title:
        print("error: provide --arxiv or --title", file=sys.stderr)
        sys.exit(2)

    result = verdict_for_arxiv(args.arxiv, args.mailto) if args.arxiv else verdict_for_title(args.title, args.mailto)
    print(f"status: {result['status']}")
    print(f"title : {result.get('title', '(n/a)')}")
    if result.get("match"):
        m = result["match"]
        print(f"match : {m['score']} | {m.get('year')} | {m.get('venue')} | {m.get('doi')}")
    if result.get("journal_ref"):
        print(f"journal_ref: {result['journal_ref']}")
    if result.get("doi"):
        print(f"doi: {result['doi']}")
    print(f"note : {result.get('note')}")

    if result["status"] == "preprint-only":
        print("\nAction: label as preprint; do NOT cite as peer-reviewed. Keep searching for a published version.")
        sys.exit(0)
    if result["status"] == "unknown":
        sys.exit(1)


if __name__ == "__main__":
    main()
