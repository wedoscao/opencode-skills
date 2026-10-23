#!/usr/bin/env python3
"""Generate per-folder README.md and a root INDEX.md from a download log.

The scripts can verify metadata but cannot invent curation, so this takes:
  --meta        {doi: {priority, role, venue, tier}}   (human judgement)
  --directions  {dir: {title, goal, reading_path}}     (folder narrative)

Priority 1 = read first (three stars), 3 = optional (one star).
"""
import argparse
import json
import os
import sys


def stars(priority):
    try:
        p = int(priority)
    except (TypeError, ValueError):
        return "⭐"
    return "⭐" * max(1, min(3, 4 - p))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--log", required=True, help="download-log.json produced by fetch_pdfs.py")
    ap.add_argument("--meta", help="JSON: {doi: {priority, role, venue, tier}}")
    ap.add_argument("--directions", help="JSON: {dir: {title, goal, reading_path}}")
    args = ap.parse_args()

    log = json.load(open(args.log, encoding="utf-8"))
    meta = json.load(open(args.meta, encoding="utf-8")) if args.meta else {}
    directions = json.load(open(args.directions, encoding="utf-8")) if args.directions else {}

    ok = [r for r in log if r.get("status") == "ok" and r.get("file")]
    missing = [r for r in log if r.get("status") != "ok"]

    folders = {}
    for rec in ok:
        folders.setdefault(rec.get("dir", "papers"), []).append(rec)

    rows = []
    for folder in sorted(folders):
        papers = sorted(
            folders[folder],
            key=lambda r: (meta.get(r["doi"], {}).get("priority", 9), (r.get("meta") or {}).get("year") or 0),
        )
        info = directions.get(folder, {})
        title = info.get("title") or folder
        goal = info.get("goal", "")
        path = info.get("reading_path", "")

        out = [f"# {title}", ""]
        if goal:
            out += [goal, ""]
        if path:
            out += [f"**Đường đọc:** {path}", ""]
        out += [f"**{len(papers)} bài** — ⭐ = mức ưu tiên đọc (3 sao = đọc trước).", ""]
        out += ["| ⭐ | Bài (file PDF) | Nguồn | Xếp hạng | Vai trò |", "|---|---|---|---|---|"]
        for rec in papers:
            m = rec.get("meta") or {}
            extra = meta.get(rec["doi"], {})
            filename = os.path.basename(rec["file"])
            role = extra.get("role") or rec.get("note", "")
            venue = extra.get("venue") or m.get("venue", "")
            tier = extra.get("tier", "")
            out.append(f"| {stars(extra.get('priority'))} | [{filename}](./{filename}) | {venue} | {tier} | {role} |")

        out += ["", "## Trích dẫn & DOI", ""]
        for rec in papers:
            m = rec.get("meta") or {}
            out.append(f"- {m.get('author', 'Anon')} et al. ({m.get('year', 'n.d.')}). "
                       f"*{m.get('title', '')}*. {m.get('venue', '')}. https://doi.org/{rec['doi']}")
        with open(os.path.join(args.root, folder, "README.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        rows.append((folder, title, len(papers)))

    index = ["# Paper library", "",
             "Papers are peer-reviewed and prioritise Scopus/Web of Science indexed venues. "
             "Quartiles are estimates from SJR/JCR at download time — re-check before submission.", "",
             "| Folder | Direction | Papers |", "|---|---|---|"]
    for folder, title, n in rows:
        index.append(f"| [`{folder}`](./{folder}/) | {title} | {n} |")
    index += ["", f"**Total: {len(ok)} PDFs.** Each folder has a README with reading order and DOIs.", ""]

    if missing:
        index += ["## Not downloaded (paywalled)", "",
                  "These need library access (OpenAthens) or a request to the authors.", "",
                  "| Paper | Venue | DOI |", "|---|---|---|"]
        for rec in missing:
            m = rec.get("meta") or {}
            index.append(f"| {m.get('title', rec['doi'])} | {m.get('venue', '')} | https://doi.org/{rec['doi']} |")
        index.append("")

    index += ["## Reading rule", "",
              "For each paper write three lines: problem, method, the limitation the authors admit. "
              "That third line is where a publishable contribution usually starts.", ""]

    with open(os.path.join(args.root, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index))

    print(f"wrote {len(rows)} folder READMEs and INDEX.md ({len(ok)} PDFs, {len(missing)} missing)")


if __name__ == "__main__":
    main()
