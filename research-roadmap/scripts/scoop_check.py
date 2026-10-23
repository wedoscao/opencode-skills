#!/usr/bin/env python3
"""Check whether a research idea has already been done recently.

Queries Crossref (published) and arXiv (preprints), ranks by title-token overlap with
the idea, and flags anything that looks close. A high overlap is not proof of a scoop —
read the abstract before panicking — but it is a cheap way to avoid spending three
months on a solved problem.

  python scoop_check.py --query "calibration of Vietnamese LLM hallucination detection" \
      --months 12 --out SCOOP.md
"""
import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; research-roadmap/1.0)"
STOP = {"the", "and", "for", "with", "from", "that", "this", "using", "based", "towards",
        "via", "into", "over", "under", "toward", "a", "an", "of", "on", "in", "to"}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s)


def tokens(s):
    return {w for w in norm(s).split() if len(w) > 3 and w not in STOP}


def overlap(a, b):
    """Plain token overlap; kept for callers that want the naive score."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta)


def idf_scores(query, titles):
    """Weight shared tokens by rarity: 'hallucination' counts, 'large language models' barely does."""
    import math
    docs = [tokens(t) for t in titles]
    n = max(1, len(docs))
    df = {}
    for doc in docs:
        for w in doc:
            df[w] = df.get(w, 0) + 1
    q = tokens(query)
    if not q:
        return []
    weights = {w: math.log((n + 1) / (df.get(w, 0) + 0.5)) for w in q}
    total = sum(weights.values()) or 1.0
    out = []
    for doc in docs:
        shared = q & doc
        out.append(round(sum(weights[w] for w in shared) / total, 2))
    return out


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")


def crossref(query, months):
    import datetime as dt
    since = (dt.date.today() - dt.timedelta(days=int(months * 30.4))).isoformat()
    url = ("https://api.crossref.org/works?" + urllib.parse.urlencode({
        "query.bibliographic": query,
        "rows": "25",
        "filter": f"from-pub-date:{since}",
        "select": "DOI,title,container-title,issued,type",
        "mailto": "research-roadmap@example.org",
    }))
    try:
        items = json.loads(get(url))["message"]["items"]
    except Exception:
        return []
    out = []
    for it in items:
        title = (it.get("title") or [""])[0]
        out.append({
            "title": title,
            "venue": (it.get("container-title") or [""])[0],
            "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
            "id": "https://doi.org/" + (it.get("DOI") or ""),
            "source": "Crossref",
        })
    return out


def arxiv(query, months):
    q = f'all:"{query}"'
    url = ("http://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(q)
           + "&sortBy=submittedDate&sortOrder=descending&max_results=25")
    try:
        xml = get(url)
    except Exception:
        return []
    out = []
    for block in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        title = re.search(r"<title>(.*?)</title>", block, re.S)
        link = re.search(r"<id>(.*?)</id>", block, re.S)
        date = re.search(r"<published>(.*?)</published>", block, re.S)
        if not title:
            continue
        out.append({
            "title": re.sub(r"\s+", " ", title.group(1)).strip(),
            "venue": "arXiv preprint",
            "year": (date.group(1)[:4] if date else ""),
            "id": link.group(1) if link else "",
            "source": "arXiv",
        })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", action="append", required=True, help="Idea description; repeatable")
    ap.add_argument("--months", type=float, default=12, help="Look-back window (default 12)")
    ap.add_argument("--threshold", type=float, default=0.5, help="Overlap that counts as 'too close'")
    ap.add_argument("--out")
    args = ap.parse_args()

    rows = []
    for q in args.query:
        hits = crossref(q, args.months) + arxiv(q, args.months)
        scores = idf_scores(q, [h["title"] for h in hits])
        for h, sc in zip(hits, scores):
            h["overlap"] = sc
            h["query"] = q
        rows.extend(hits)
        time.sleep(0.4)

    seen, unique = set(), []
    for r in sorted(rows, key=lambda x: -x["overlap"]):
        key = norm(r["title"])[:80]
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)

    top = [r for r in unique if r["overlap"] >= 0.15][:15]
    lines = ["# Scoop check", "",
             f"Truy vấn: {', '.join(args.query)} · cửa sổ {args.months:g} tháng · "
             f"ngưỡng cảnh báo {args.threshold}", "",
             "| Overlap | Năm | Nguồn | Venue | Tiêu đề |", "|---|---|---|---|---|"]
    for r in top:
        flag = " ⚠" if r["overlap"] >= args.threshold else ""
        lines.append(f"| {r['overlap']:.2f}{flag} | {r['year']} | {r['source']} | {r['venue'][:34]} | [{r['title'][:74]}]({r['id']}) |")

    close = [r for r in top if r["overlap"] >= args.threshold]
    lines += ["", "## Đọc gì trước", ""]
    if close:
        lines.append(f"Có **{len(close)} bài** vượt ngưỡng. Đọc abstract của các bài ⚠ trước khi cam kết:")
        lines.append("")
        lines.append("Câu hỏi cần trả lời cho mỗi bài: *họ giải quyết đúng bài toán của mình chưa, "
                     "và nếu chưa thì thiếu cái gì?* Nếu câu trả lời là \"đã giải quyết rồi\" → đổi góc.")
    else:
        lines.append("Không có bài nào vượt ngưỡng trong cửa sổ thời gian này. Điều đó **không** chứng minh "
                     "ý tưởng mới — chỉ là chưa thấy ai dùng đúng từ khoá. Thử thêm 2–3 cách diễn đạt khác.")
    lines += ["", "> Lưu ý: so khớp chỉ dựa trên tiêu đề. Đây là bộ lọc thô để tiết kiệm thời gian, "
                  "không thay được việc đọc related work.", ""]

    text = "\n".join(lines)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
        print(f"wrote {args.out} ({len(top)} candidates, {len(close)} above threshold)")
    else:
        print(text)


if __name__ == "__main__":
    main()
