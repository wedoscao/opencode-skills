#!/usr/bin/env python3
"""Scaffold a research roadmap from an intent file.

Creates seven files whose skeletons encode the rigour required by the chosen target
(thesis, domestic conference, international conference, Q1–Q2 journal, Q3–Q4 journal,
grant). Filling them requires judgement; the script only guarantees structure and that
the hard questions are asked.

  python scaffold.py --intent intent.json --out ./roadmap
"""
import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import build_roadmap  # noqa: E402


def load_targets():
    path = os.path.join(HERE, "..", "references", "targets.json")
    return json.load(open(path, encoding="utf-8"))


def infer_target(intent, targets):
    """Pick a target from constraints when the user has not chosen one."""
    months = float(intent.get("months") or 6)
    compute = (intent.get("compute") or "").lower()
    level = (intent.get("level") or "").lower()
    has_gpu = any(k in compute for k in ("3090", "4090", "a100", "v100", "gpu", "colab"))
    if intent.get("target") in targets:
        return intent["target"], "do người dùng chọn"
    if months <= 5 or level == "beginner":
        return "thesis", f"suy ra: {months:g} tháng và trình độ '{level or 'chưa rõ'}'"
    if months <= 7:
        return "conf-domestic", f"suy ra: {months:g} tháng"
    if months >= 11 and has_gpu:
        return "journal-q1q2", f"suy ra: {months:g} tháng + có GPU"
    return "journal-q3q4", f"suy ra: {months:g} tháng"


def proposal(intent, t, target_key, why):
    months = intent.get("months") or t["months_default"]
    return f"""# Đề cương nghiên cứu

**Hướng:** {intent.get('direction', 'TODO')}  
**Mục tiêu công bố:** {t['label']} *(chọn: {why})*  
**Thời lượng:** {months:g} tháng · **Compute:** {intent.get('compute', 'TODO')} · **Dữ liệu:** {intent.get('data', 'TODO')}

## 1. Vấn đề
<!-- 3–5 câu. Nêu hiện tượng cụ thể, không nêu tên phương pháp. -->
TODO

## 2. Khoảng trống
<!-- Tóm tắt từ GAP-TABLE.csv: 3 hạn chế lặp lại ở nhiều paper. -->
- TODO
- TODO
- TODO

## 3. Câu hỏi nghiên cứu
**RQ1:** TODO (một câu, có thể trả lời bằng thực nghiệm)
**RQ2 (tuỳ chọn):** TODO

## 4. Đóng góp dự kiến ({t['contributions']} đóng góp)
1. TODO — *được chứng minh bởi bảng/hình nào?*
2. TODO

## 5. Phạm vi — và những gì **không** làm
- Trong phạm vi: TODO
- Ngoài phạm vi: TODO *(ghi rõ để tránh bị hỏi ngoài đề)*

## 6. Ràng buộc thực tế
| Ràng buộc | Giá trị | Ảnh hưởng lên thiết kế |
|---|---|---|
| Thời gian | {months:g} tháng | |
| Compute | {intent.get('compute', 'TODO')} | |
| Dữ liệu | {intent.get('data', 'TODO')} | |
| Trình độ hiện tại | {intent.get('level', 'TODO')} | |

## 7. Tiêu chí thành công
<!-- Lấy từ gate của profile; đây là thứ dùng để tự đánh giá, không phải lời hứa. -->
{chr(10).join('- ' + g for g in t['gates'])}
"""


def gap_table(intent):
    # No comment lines: a CSV with '#' rows breaks pandas/R readers silently.
    return "paper,year,venue,problem,method,stated_limitation,your_angle,priority\n"


def experiments(intent, t):
    return f"""# Kế hoạch thực nghiệm

Mức tối thiểu cho **{t['label']}**: {t['baselines']} baseline · {t['datasets']} dataset · {t['ablations']} ablation · {t['seeds']} seed.

## 1. Dataset
| Dataset | Quy mô | Chia tập | Truy cập | Vai trò |
|---|---|---|---|---|
| TODO | | | công khai / xin phép | train / test / cross-domain |

## 2. Baseline
| Baseline | Năm | Venue | Có code? | Tái lập được? | Ghi chú |
|---|---|---|---|---|---|
| TODO | | | | ☐ | |

> Baseline phải mạnh và **cùng ngân sách** (cùng backbone, cùng số tham số, cùng số epoch). So sánh lệch điều kiện sẽ bị bắt lỗi ở vòng review.

## 3. Ma trận thực nghiệm chính
| Phương pháp | Dataset A | Dataset B | Dataset C | Ghi chú |
|---|---|---|---|---|
| Baseline 1 | | | | |
| **Đề xuất** | | | | |

## 4. Ablation
| Thành phần bỏ đi | Kỳ vọng | Kết quả | Kết luận |
|---|---|---|---|
| TODO | | | |

## 5. Metric & kiểm định
- Metric chính: TODO · Metric phụ: TODO
- Số seed: {t['seeds']} → báo cáo mean ± std
- Kiểm định: {'có (Wilcoxon / bootstrap CI)' if t['stats'] else 'chưa bắt buộc ở mức này'}

## 6. Ngân sách compute (ước lượng)
| Hạng mục | Giờ GPU | Ghi chú |
|---|---|---|
| Tái lập baseline | | |
| Thí nghiệm chính | | |
| Ablation | | |
| Dự phòng (30%) | | |
"""


def target_file(intent, t, target_key):
    return f"""# Mục tiêu công bố

**Profile:** {t['label']} (`{target_key}`)  
**Định dạng:** {t['pages']} · **Review:** {t['review']}  
**Sản phẩm cần nộp:** {', '.join(t['deliverables'])}

## Yêu cầu tối thiểu
| Hạng mục | Mức cần đạt |
|---|---|
| Đóng góp | {t['contributions']} |
| Baseline | {t['baselines']} |
| Dataset | {t['datasets']} |
| Ablation | {t['ablations']} |
| Seed | {t['seeds']} |
| Kiểm định thống kê | {'bắt buộc' if t['stats'] else 'không bắt buộc'} |

## Danh sách venue (điền sau khi chạy venue_check.py)
| Venue | ISSN | Scope fit (1–5) | APC | Thời gian review | Cờ đỏ | Ghi chú |
|---|---|---|---|---|---|---|
| TODO | | | | | | |

## Cảnh báo
- **Quartile không được xác minh tự động.** Scopus/JCR là nguồn duy nhất đáng tin và thay đổi theo năm; script chỉ tra ISSN, DOAJ và APC.
- Tạp chí nhận bài < 3 tuần, APC cao bất thường, hoặc không có trong DOAJ dù quảng cáo "open access" → kiểm tra kỹ trước khi nộp.
- Hỏi GVHD: nhóm có bài Q1/Q2 nào trong 2 năm gần đây, và có thể tham gia không.
"""


def risks(intent, t):
    return f"""# Rủi ro & phương án

| Rủi ro | Khả năng | Tác động | Dấu hiệu sớm | Phương án |
|---|---|---|---|---|
| Bị scoop (có paper gần trùng) | Trung bình | Cao | Scoop-check thấy overlap > 0.5 | Đổi góc, thêm phân tích mà bài kia không có |
| Không tái lập được baseline | Trung bình | Cao | Quá 3 tuần vẫn lệch >2 điểm | Liên hệ tác giả; chuyển baseline đơn giản hơn |
| Kết quả không vượt baseline | Cao | Cao | Gate pha 3 không đạt | Thu hẹp claim; chuyển sang phân tích/benchmark paper |
| Mất quyền truy cập dữ liệu | Thấp–TB | Cao | Chưa có approval sau 4 tuần | Dùng dataset công khai thay thế ngay từ đầu |
| Thiếu compute | Trung bình | TB | Hàng đợi > 2 ngày/job | Giảm quy mô model, dùng subset, thuê GPU theo giờ |
| Reviewer đòi so sánh mới | Cao | TB | — | Chuẩn bị sẵn 1 baseline dự phòng chưa đưa vào bản chính |
| Viết quá sát deadline | Cao | TB | Còn < 3 tuần mà chưa có bản đầy đủ | Viết song song từ pha 3, không đợi có kết quả |

## Rủi ro đặc thù của {t['label']}
- TODO
"""


def outline(intent, t):
    return f"""# Dàn ý bản thảo ({t['pages']})

| Section | Nội dung | Độ dài | Hình/bảng cần có |
|---|---|---|---|
| Abstract | Vấn đề → cách làm → kết quả định lượng → ý nghĩa | 150–250 từ | — |
| 1. Introduction | Vì sao bây giờ, vì sao khó, đóng góp | 1–1.5 trang | Hình minh hoạ bài toán |
| 2. Related Work | 3 nhóm, mỗi nhóm 1 câu "khác gì chúng tôi" | 1.5–2 trang | Bảng so sánh |
| 3. Method | Đủ để người khác cài lại | 3–4 trang | Sơ đồ kiến trúc |
| 4. Experiments | Setup, kết quả chính, ablation, phân tích lỗi | 3–5 trang | Bảng chính + 2–3 hình |
| 5. Discussion | Khi nào phương pháp thất bại | 0.5–1 trang | — |
| 6. Limitations | Viết thật, đừng giấu | 0.3 trang | — |
| 7. Conclusion | Không thêm claim mới | 0.3 trang | — |
| References | | | |

## Quy tắc viết
- Mỗi câu trong Abstract phải truy được về một bảng hoặc hình.
- Không dùng "significantly" nếu chưa có kiểm định thống kê.
- Bảng kết quả phải ghi rõ số seed và độ lệch chuẩn.
"""


def readme(intent, t, target_key):
    return f"""# Research roadmap — {intent.get('direction', 'TODO')}

Sinh ngày {dt.date.today().isoformat()} cho mục tiêu **{t['label']}**.

| File | Dùng để |
|---|---|
| `PROPOSAL.md` | Đề cương: vấn đề, gap, RQ, đóng góp, phạm vi |
| `GAP-TABLE.csv` | Chỗ chen vào, rút từ thư viện paper |
| `EXPERIMENTS.md` | Dataset, baseline, ablation, ngân sách GPU |
| `TARGET.md` | Yêu cầu của profile + danh sách venue |
| `ROADMAP.md` | Sprint 2 tuần + gate |
| `RISKS.md` | Rủi ro và phương án |
| `OUTLINE.md` | Dàn ý bản thảo |

## Cách điền `GAP-TABLE.csv`

Một dòng một paper. Cột `stated_limitation` phải là câu **tác giả tự viết** trong paper, không phải bạn suy diễn —
nếu không trích được thì chưa đọc đủ kỹ. Cột `your_angle` là chỗ bạn chen vào. `priority` 1 = đọc trước.

## Việc tiếp theo (theo thứ tự)
1. Điền `GAP-TABLE.csv` từ thư viện paper — không điền thì các file sau đều là suy đoán.
2. Chạy `scoop_check.py` cho ý tưởng chính, đọc 10 bài gần nhất.
3. Chốt RQ1, rồi mới điền `EXPERIMENTS.md`.
4. Chạy `venue_check.py` cho 3–5 venue, tự xác minh quartile trên Scopus/JCR.
5. Đưa `PROPOSAL.md` cho GVHD trước khi cam kết mốc thời gian.

> Các file này là **khung**, không phải bản thảo. Chỗ nào còn `TODO` là chỗ chưa có quyết định.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--intent", required=True, help="JSON: direction, months, target, compute, data, level")
    ap.add_argument("--out", required=True, help="Directory to write the seven files into")
    args = ap.parse_args()

    intent = json.load(open(args.intent, encoding="utf-8"))
    targets = load_targets()
    target_key, why = infer_target(intent, targets)
    t = targets[target_key]
    months = float(intent.get("months") or t["months_default"])
    start = intent.get("start") or dt.date.today().isoformat()

    os.makedirs(args.out, exist_ok=True)
    files = {
        "README.md": readme(intent, t, target_key),
        "PROPOSAL.md": proposal(intent, t, target_key, why),
        "GAP-TABLE.csv": gap_table(intent),
        "EXPERIMENTS.md": experiments(intent, t),
        "TARGET.md": target_file(intent, t, target_key),
        "RISKS.md": risks(intent, t),
        "OUTLINE.md": outline(intent, t),
        "ROADMAP.md": build_roadmap(months, start, t["label"]),
    }
    for name, content in files.items():
        open(os.path.join(args.out, name), "w", encoding="utf-8").write(content)

    todos = sum(c.count("TODO") for c in files.values())
    print(f"{len(files)} files → {args.out}")
    print(f"profile: {target_key} ({why}) · {months:g} months · {todos} TODOs to resolve")


if __name__ == "__main__":
    main()
