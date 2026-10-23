#!/usr/bin/env python3
"""Look up a journal's identifiers and open-access status before you submit.

What this can verify: ISSN, publisher, title (Crossref), DOAJ listing, APC.
What it cannot verify: Scopus/WoS indexing or quartile. Those live behind Scopus/JCR,
change yearly, and must be checked by the author. The report says so explicitly so no
one mistakes this output for an indexing guarantee.

  python venue_check.py --name "Language Resources and Evaluation"
  python venue_check.py --issn 1574-020X
"""
import argparse
import json
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; research-roadmap/1.0)"


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def crossref_journal(name=None, issn=None):
    if issn:
        url = f"https://api.crossref.org/journals/{urllib.parse.quote(issn)}"
        try:
            return [get(url)["message"]]
        except Exception:
            return []
    url = "https://api.crossref.org/journals?" + urllib.parse.urlencode({"query": name, "rows": "5"})
    try:
        return get(url)["message"]["items"]
    except Exception:
        return []


def doaj(issn):
    try:
        data = get("https://doaj.org/api/search/journals/" + urllib.parse.quote(f"issn:{issn}"))
    except Exception:
        return None
    if not data.get("results"):
        return None
    j = data["results"][0]["bibjson"]
    apc = j.get("apc") or {}
    price = ""
    if apc.get("has_apc") and apc.get("max"):
        m = apc["max"][0]
        price = f"{m.get('price')} {m.get('currency')}"
    elif apc.get("has_apc") is False:
        price = "không APC"
    return {"title": j.get("title"), "apc": price, "url": apc.get("url", ""),
            "publisher": (j.get("publisher") or {}).get("name", "")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", help="Journal title")
    ap.add_argument("--issn", help="ISSN (preferred when you already know it)")
    ap.add_argument("--out")
    args = ap.parse_args()
    if not args.name and not args.issn:
        ap.error("provide --name or --issn")

    journals = crossref_journal(args.name, args.issn)
    if not journals:
        print("Không tìm thấy journal trong Crossref. Kiểm tra lại tên/ISSN.")
        return 1

    lines = ["# Kiểm tra venue", "",
             "| Journal | ISSN | Publisher | Trong DOAJ | APC |",
             "|---|---|---|---|---|"]
    details = []
    for j in journals[:5]:
        title = j.get("title", "")
        issns = j.get("ISSN") or []
        publisher = j.get("publisher", "")
        d = doaj(issns[0]) if issns else None
        lines.append(f"| {title} | {', '.join(issns)} | {publisher[:34]} | "
                     f"{'có' if d else 'không thấy'} | {(d or {}).get('apc', '?')} |")
        details.append((title, issns, d))

    lines += ["", "> Không thấy trong DOAJ thường chỉ có nghĩa là tạp chí lai (hybrid) hoặc không nộp APC — "
                  "không tự nó là dấu hiệu xấu. Chỉ coi là cờ đỏ khi tạp chí *tự nhận* open access mà vẫn không có trong DOAJ.", ""]
    lines += ["## Cờ đỏ cần tự kiểm tra", "",
              "- **Quartile**: script này không tra được. Dùng Scopus Sources hoặc JCR; quartile đổi theo năm và theo category.",
              "- **Thời gian review**: không có nguồn mở đáng tin; hỏi GVHD hoặc đồng nghiệp đã nộp.",
              "- **APC cao bất thường + nhận bài rất nhanh**: dấu hiệu tạp chí cần tránh, kể cả khi có trong DOAJ.",
              "- **Không có trong DOAJ nhưng tự nhận open access**: kiểm tra trang tạp chí và danh sách cảnh báo.",
              ""]

    text = "\n".join(lines)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
        print(text)
        print(f"\nwrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    raise SystemExit(main())
