# -*- coding: utf-8 -*-
"""make_report.py —— 把评测原始记录生成 HTML 可视化报告（浏览器双击可看）。

用法：
    .\\.venv\\Scripts\\python.exe scripts\\make_report.py
    .\\.venv\\Scripts\\python.exe scripts\\make_report.py --file docs/eval/测试结果/原始记录_xxx.jsonl

产出：
    docs/eval/测试结果/评测报告_[标签_]时间戳.html

设计要点：
    左栏"预期"（本题考什么、应包含哪些关键词），右栏"实际"（完整回答 + 引用原文片段）；
    挂题整卡标红，方便一眼定位；统计信息在页头。
"""

import argparse
import html
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULT_DIR = ROOT / "docs" / "eval" / "测试结果"

EXPECT_LABEL = {
    "answer": "应含关键词",
    "no_answer": "应拒绝作答（不编造）",
    "conflict": "应识别资料冲突",
}
GRADE_COLOR = {"PASS": "#16a34a", "FAIL": "#dc2626", "ERROR": "#d97706"}
GRADE_BG = {"PASS": "#f0fdf4", "FAIL": "#fef2f2", "ERROR": "#fffbeb"}


def esc(text) -> str:
    return html.escape(str(text or ""))


def load_records(path: Path) -> list:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def build_sources_html(sources: list) -> str:
    if not sources:
        return '<div class="none">无引用</div>'
    blocks = []
    for s in sources:
        page = s.get("page")
        page_txt = f"第 {page} 页" if page is not None else "页码未知"
        text = esc((s.get("text") or "")[:280])
        blocks.append(
            f'<div class="source"><div class="source-head">📄 {esc(s.get("filename"))}'
            f' · {page_txt}</div><div class="source-text">…{text}…</div></div>'
        )
    return "".join(blocks)


def build_card(rec: dict) -> str:
    grade = rec.get("grade", "ERROR")
    color = GRADE_COLOR.get(grade, "#64748b")
    bg = GRADE_BG.get(grade, "#f8fafc")
    must = rec.get("must_contain") or []
    expect = EXPECT_LABEL.get(rec.get("expect"), rec.get("expect", ""))
    must_html = "".join(f'<span class="kw">{esc(kw)}</span>' for kw in must) or '<span class="none">—</span>'
    subs = rec.get("sub_questions") or []
    subs_html = ("<div class=\"subs\">🔀 拆分：" + " ／ ".join(esc(s) for s in subs) + "</div>") if len(subs) > 1 else ""
    answer = esc(rec.get("answer", "")).replace("\n", "<br>")

    return f"""
    <div class="card" style="border-left:6px solid {color};background:{bg}">
      <div class="card-head">
        <span class="qid">{esc(rec.get('id'))}</span>
        <span class="cat">{esc(rec.get('category'))}</span>
        <span class="badge" style="background:{color}">{esc(grade)}</span>
        <span class="meta">{rec.get('elapsed_ms', 0)} ms · 调用≈{rec.get('est_calls', 1)} 次</span>
      </div>
      <div class="question">问：{esc(rec.get('question'))}</div>
      <div class="cols">
        <div class="col">
          <div class="col-title">预期（判分标准）</div>
          <div class="expect">{esc(expect)}</div>
          <div class="kwbox">{must_html}</div>
          <div class="detail">判定说明：{esc(rec.get('detail'))}</div>
        </div>
        <div class="col">
          <div class="col-title">实际（AI 回答）</div>
          <div class="answer">{answer}</div>
          {subs_html}
        </div>
      </div>
      <div class="col-title" style="margin-top:10px">引用原文（AI 实际用到的片段）</div>
      {build_sources_html(rec.get('sources') or [])}
    </div>
    """


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 HTML 评测报告")
    parser.add_argument("--file", type=str, default="", help="指定原始记录 jsonl；默认取最新")
    args = parser.parse_args()

    if args.file:
        raw_path = Path(args.file)
        if not raw_path.is_absolute():
            raw_path = ROOT / raw_path
    else:
        candidates = sorted(RESULT_DIR.glob("原始记录_*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            raise SystemExit("未找到原始记录，先跑 run_eval.py")
        raw_path = candidates[-1]  # 按修改时间取最近一次评测

    records = load_records(raw_path)
    total = len(records)
    passed = sum(1 for r in records if r.get("grade") == "PASS")
    errors = sum(1 for r in records if r.get("grade") == "ERROR")
    avg_ms = sum(r.get("elapsed_ms", 0) for r in records) / max(total, 1)
    calls = sum(r.get("est_calls", 1) for r in records)

    by_cat = {}
    for r in records:
        c = by_cat.setdefault(r.get("category", "未分类"), [0, 0])
        c[1] += 1
        c[0] += 1 if r.get("grade") == "PASS" else 0
    cat_html = "".join(
        f'<div class="stat"><div class="stat-num">{p}/{t}</div><div class="stat-label">{esc(cat)}</div></div>'
        for cat, (p, t) in by_cat.items()
    )

    cards = "\n".join(build_card(r) for r in records)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    tag = raw_path.stem.replace("原始记录_", "")
    out_path = RESULT_DIR / f"评测报告_{tag}.html"

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>RAG 评测报告 {stamp}</title>
<style>
  body {{ font-family: "Microsoft YaHei", "PingFang SC", sans-serif; margin: 0; background: #f1f5f9; color: #0f172a; }}
  .wrap {{ max-width: 1180px; margin: 0 auto; padding: 28px 20px 60px; }}
  h1 {{ font-size: 24px; margin: 0 0 6px; }}
  .sub {{ color: #64748b; font-size: 13px; margin-bottom: 18px; }}
  .summary {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 24px; }}
  .stat {{ background: #fff; border-radius: 10px; padding: 12px 18px; box-shadow: 0 1px 3px rgba(15,23,42,.08); min-width: 120px; }}
  .stat-num {{ font-size: 22px; font-weight: 700; color: #1d4ed8; }}
  .stat-label {{ font-size: 12px; color: #64748b; }}
  .card {{ background: #fff; border-radius: 12px; padding: 16px 18px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(15,23,42,.08); }}
  .card-head {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .qid {{ font-weight: 700; font-size: 16px; }}
  .cat {{ background: #e0e7ff; color: #3730a3; border-radius: 6px; padding: 2px 8px; font-size: 12px; }}
  .badge {{ color: #fff; border-radius: 6px; padding: 2px 10px; font-size: 12px; font-weight: 700; }}
  .meta {{ margin-left: auto; color: #64748b; font-size: 12px; }}
  .question {{ font-size: 15px; font-weight: 600; margin: 10px 0 12px; }}
  .cols {{ display: flex; gap: 14px; flex-wrap: wrap; }}
  .col {{ flex: 1 1 320px; background: #f8fafc; border-radius: 8px; padding: 10px 12px; }}
  .col-title {{ font-size: 12px; color: #64748b; margin-bottom: 6px; font-weight: 700; }}
  .expect {{ font-size: 13px; margin-bottom: 8px; }}
  .kwbox {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }}
  .kw {{ background: #dbeafe; color: #1e40af; border-radius: 4px; padding: 1px 7px; font-size: 12px; }}
  .detail {{ font-size: 12px; color: #475569; }}
  .answer {{ font-size: 13px; line-height: 1.7; white-space: normal; }}
  .subs {{ margin-top: 8px; font-size: 12px; color: #1d4ed8; background: #eff6ff; border-radius: 6px; padding: 6px 8px; }}
  .source {{ border-top: 1px dashed #cbd5e1; padding: 8px 0; }}
  .source-head {{ font-size: 12px; font-weight: 700; color: #334155; }}
  .source-text {{ font-size: 12px; color: #475569; margin-top: 3px; line-height: 1.6; }}
  .none {{ font-size: 12px; color: #94a3b8; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>RAG 产品咨询助手 · 评测报告</h1>
  <div class="sub">数据来源：{esc(raw_path.name)} ｜ 生成时间：{stamp} ｜ 平均耗时 {avg_ms/1000:.1f}s/题 ｜ 模型调用约 {calls} 次</div>
  <div class="summary">
    <div class="stat"><div class="stat-num">{passed}/{total}</div><div class="stat-label">总分</div></div>
    <div class="stat"><div class="stat-num">{errors}</div><div class="stat-label">请求错误</div></div>
    {cat_html}
  </div>
  {cards}
</div>
</body>
</html>
"""
    out_path.write_text(page, encoding="utf-8")
    print(f"HTML 报告已生成：{out_path}")
    print(f"共 {total} 题：PASS {passed} / ERROR {errors}")


if __name__ == "__main__":
    main()
