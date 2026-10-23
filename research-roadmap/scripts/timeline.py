#!/usr/bin/env python3
"""Generate a sprint plan with go/no-go gates from a month budget.

The point of gates is to make stopping cheap: a project that fails at month 3 is a
lesson, one that fails at month 9 is a lost year.

CLI:
  python timeline.py --months 9 --start 2026-11-02 --target journal-q1q2 --out ROADMAP.md
"""
import argparse
import datetime as dt
import math

PHASES = [
    ("Nền tảng & gap", 0.15, "Bảng gap + 3 baseline tái lập được",
     "Đọc đủ 30–40 paper, viết được gap bằng 1 câu, tái lập 1 baseline"),
    ("Tái lập baseline", 0.20, "Baseline reproduce ±1 điểm",
     "Chạy lại được trên máy sạch, log kết quả có seed"),
    ("Phương pháp & thí nghiệm chính", 0.30, "Kết quả chính trên toàn bộ dataset",
     "Có ít nhất 1 cấu hình vượt baseline; nếu không, đổi hướng ngay"),
    ("Ablation & kiểm định", 0.15, "Bảng ablation + kiểm định thống kê",
     "Chứng minh từng thành phần có tác dụng, không chỉ 'đẹp hơn'"),
    ("Viết", 0.15, "Bản thảo hoàn chỉnh",
     "Mỗi claim trong abstract có bảng/hình tương ứng"),
    ("Nộp & phản hồi", 0.05, "Submission + bộ thí nghiệm dự phòng",
     "Sẵn sàng trả lời 3 câu hỏi reviewer khó nhất"),
]


def build_roadmap(months, start, target_label=""):
    start = dt.date.fromisoformat(start) if isinstance(start, str) else start
    total_days = int(months * 30.4)
    sprints = max(4, math.ceil(total_days / 14))
    rows = []
    idx = 0
    for phase, share, artifact, gate in PHASES:
        n = max(1, round(sprints * share))
        for _ in range(n):
            if idx >= sprints:
                break
            s = start + dt.timedelta(days=14 * idx)
            e = s + dt.timedelta(days=13)
            rows.append((idx + 1, s, e, phase, artifact, ""))
            idx += 1
    while idx < sprints:
        s = start + dt.timedelta(days=14 * idx)
        e = s + dt.timedelta(days=13)
        rows.append((idx + 1, s, e, "Đệm / dự phòng", "Xử lý phát sinh", ""))
        idx += 1

    lines = [f"# Roadmap {months:g} tháng" + (f" — {target_label}" if target_label else ""), "",
             f"Bắt đầu: {start.isoformat()} · Kết thúc dự kiến: {(start + dt.timedelta(days=total_days)).isoformat()} · {sprints} sprint × 2 tuần", "",
             "| Sprint | Từ | Đến | Pha | Artifact | Gate |", "|---|---|---|---|---|---|"]
    phase_seen = set()
    for n, s, e, phase, artifact, _ in rows:
        gate = ""
        label = artifact
        if phase not in phase_seen:
            phase_seen.add(phase)
            gate = next((g for p, _, _, g in PHASES if p == phase), "")
        else:
            label = "↳"
            phase = ""
        lines.append(f"| {n} | {s.strftime('%d/%m')} | {e.strftime('%d/%m')} | {phase} | {label} | {gate} |")

    lines += ["", "## Cách dùng gate", "",
              "Gate là điều kiện **dừng hoặc đổi hướng**, không phải checklist để tự khen. "
              "Nếu hết pha mà gate chưa đạt, ghi lại lý do rồi quyết định: thu hẹp phạm vi, đổi baseline, "
              "hoặc đổi câu hỏi nghiên cứu. Kéo dài thêm 2 sprint mà không đổi gì là cách tốn kém nhất.", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--months", type=float, required=True)
    ap.add_argument("--start", default=dt.date.today().isoformat())
    ap.add_argument("--target", default="")
    ap.add_argument("--label", default="")
    ap.add_argument("--out")
    args = ap.parse_args()
    text = build_roadmap(args.months, args.start, args.label or args.target)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
