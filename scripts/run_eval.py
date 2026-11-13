"""对 18 道开发题跑自动化摸底评测（RAG 基线成绩单）。

用法：
    .\\.venv\\Scripts\\python.exe scripts\\run_eval.py
    .\\.venv\\Scripts\\python.exe scripts\\run_eval.py --top-k 3 --limit 8 --tag topk3
    .\\.venv\\Scripts\\python.exe scripts\\run_eval.py --ids D-01,D-06,D-14

参数：
    --top-k   每次检索几段资料（默认 4，做参数对照实验用）
    --limit   只跑前 N 题（省钱做小样本对照）
    --ids     只跑指定题号（逗号分隔）
    --tag     文件名标签（如 topk3 → 成绩单_topk3_时间戳.csv）

前置条件：
    服务已启动且 LLM_PROVIDER=deepseek（生成模式）；
    语料已批量入库（upload_corpus.py）。

产出：
    docs/eval/测试结果/成绩单[_标签]_时间戳.csv        成绩单（Excel 可直接打开）
    docs/eval/测试结果/原始记录[_标签]_时间戳.jsonl    原始回答与引用（排查用）

成绩单新增列：耗时(ms)、估算模型调用次数、拆分子问题列表（Day6）。
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8000"
QUESTIONS = ROOT / "docs" / "eval" / "questions_dev.json"
RESULT_DIR = ROOT / "docs" / "eval" / "测试结果"
CHAT_TIMEOUT = 120
SLEEP_BETWEEN = 1.0  # 每题间隔，避免请求过密

# expect=no_answer 的判分：命中任一否定表述 = 合格（没瞎编）
NO_ANSWER_PATTERNS = [
    "未提及", "未提供", "没有提及", "未找到", "没有找到", "资料中未",
    "资料未", "没有相关", "未介绍", "没有说明", "不讨论", "不保证",
    "无法回答", "没有记载", "没有写", "未包含", "无此",
    # 2026-11-10 补：D-18 冤案教训——AI 会说"无法从提供的文档中找到"
    "无法从", "无法找到", "找不到", "无法确认", "无法确定", "检索不到",
    # 2026-11-11 补：D-17 冤案教训——整词匹配抓不住"未说明"和隔字否定
    "未说明", "不能确认", "无法判断", "无从",
]
# 正则兜底："无法…确认"这类中间隔字的否定（整词匹配的天敌）
NO_ANSWER_REGEX = [
    r"无法[\s\S]{0,15}?(确认|确定|回答|判断|找到)",
    r"未[\s\S]{0,6}?(提及|说明|提供|介绍|包含|记载)",
]
# expect=conflict 的判分：报冲突的表述词（两个数字则由脚本单独比对）
CONFLICT_WORDS = ["冲突", "矛盾", "不一致", "以说明书为准", "以说明书版本为准"]


def norm(text: str) -> str:
    """去掉所有空白再比较：'24 个月' 和 '24个月' 视为相同。"""
    return (text or "").replace(" ", "").replace("\u3000", "")


def check_health() -> None:
    try:
        requests.get(f"{BASE}/health", timeout=5).raise_for_status()
    except Exception as exc:
        print(f"[前置失败] 服务未就绪: {exc}")
        sys.exit(1)


def ask(question: str, top_k: int = 4) -> dict:
    resp = requests.post(
        f"{BASE}/api/v1/chat",
        json={"question": question, "top_k": top_k},
        timeout=CHAT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def grade(item: dict, answer: str) -> tuple:
    """返回 (grade, detail)。grade: PASS / FAIL / ERROR"""
    a = norm(answer)
    expect = item["expect"]

    if expect == "answer":
        missing = [kw for kw in item["must_contain"] if norm(kw) not in a]
        if not missing:
            return "PASS", "包含全部关键词"
        return "FAIL", f"缺少关键词: {missing}"

    if expect == "no_answer":
        hit = [p for p in NO_ANSWER_PATTERNS if p in a]
        regex_hit = next((r"正则: 无法…确认类" for rx in NO_ANSWER_REGEX
                          if re.search(rx, a)), None)
        if hit or regex_hit:
            return "PASS", f"命中否定表述: {hit[0] if hit else regex_hit}"
        return "FAIL", "未见否定表述，疑似编造了答案"

    if expect == "conflict":
        nums = ["24", "36"]
        has_both = all(n in a for n in nums)
        words = [w for w in CONFLICT_WORDS if norm(w) in a]
        if has_both or words:
            return "PASS", ("同时提到两个数字" if has_both else f"命中冲突表述: {words}")
        return "FAIL", "未报告冲突（可能只挑了一个数字作答）"

    return "ERROR", f"未知 expect 类型: {expect}"


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG 评测（支持 top_k 对照实验）")
    parser.add_argument("--top-k", type=int, default=4, help="每次检索几段资料（默认 4）")
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 题（0=全部）")
    parser.add_argument("--ids", type=str, default="", help="只跑指定题号，逗号分隔")
    parser.add_argument("--tag", type=str, default="", help="文件名标签，如 topk3")
    args = parser.parse_args()

    check_health()
    items = json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    if args.ids:
        wanted = {x.strip() for x in args.ids.split(",") if x.strip()}
        items = [it for it in items if it["id"] in wanted]
    if args.limit:
        items = items[: args.limit]
    print(f"加载 {len(items)} 道题（top_k={args.top_k}），开始评测...\n")

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    tag = f"{args.tag}_" if args.tag else ""
    csv_path = RESULT_DIR / f"成绩单_{tag}{stamp}.csv"
    raw_path = RESULT_DIR / f"原始记录_{tag}{stamp}.jsonl"

    rows = []
    errors = 0

    with raw_path.open("w", encoding="utf-8") as raw_fh:
        for i, item in enumerate(items, 1):
            qid = item["id"]
            started = time.time()
            data = {}
            try:
                data = ask(item["question"], top_k=args.top_k)
                answer = data.get("answer", "")
                sources = [
                    f"{s.get('filename')} 第{s.get('page')}页"
                    for s in data.get("sources", [])
                ]
                grade_, detail = grade(item, answer)
            except Exception as exc:
                answer, sources = f"<请求失败: {str(exc)[:120]}>", []
                grade_, detail = "ERROR", "请求失败"
                errors += 1
            elapsed_ms = int((time.time() - started) * 1000)

            # 估算模型调用次数：每个子问题回答 1 次；被拆分时拆分本身再 1 次
            subs = data.get("sub_questions") or []
            est_calls = len(subs) if subs else 1
            if len(subs) > 1:
                est_calls += 1

            print(f"[{i}/{len(items)}] {qid} {grade_:4s} | {detail} | {elapsed_ms}ms")
            rows.append({
                "id": qid,
                "category": item["category"],
                "expect": item["expect"],
                "grade": grade_,
                "detail": detail,
                "question": item["question"],
                "answer": answer[:500],
                "sources": " ; ".join(sources),
                "耗时ms": elapsed_ms,
                "模型调用(估)": est_calls,
                "子问题": " / ".join(subs),
            })
            raw_fh.write(json.dumps({
                "id": qid, "question": item["question"],
                "answer": answer, "sources": data.get("sources", []),
                "sub_questions": subs, "grade": grade_, "detail": detail,
                "elapsed_ms": elapsed_ms, "est_calls": est_calls,
                "expect": item["expect"], "category": item["category"],
                "must_contain": item.get("must_contain", []),
            }, ensure_ascii=False) + "\n")

            if i < len(items):
                time.sleep(SLEEP_BETWEEN)

    # 写 CSV（utf-8-sig 让 Excel 直接打开不乱码）
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # 汇总
    total = len(rows)
    graded = [r for r in rows if r["grade"] in ("PASS", "FAIL")]
    passed = sum(1 for r in graded if r["grade"] == "PASS")
    print(f"\n===== 成绩单 =====")
    print(f"总分: {passed}/{total} ({passed / total:.0%})  [ERROR {errors} 题不计入正确率]")
    by_cat = {}
    for r in graded:
        c = by_cat.setdefault(r["category"], [0, 0])
        c[0] += 1 if r["grade"] == "PASS" else 0
        c[1] += 1
    for cat, (p, t) in by_cat.items():
        print(f"  {cat}: {p}/{t}")
    avg_ms = sum(r["耗时ms"] for r in rows) / max(len(rows), 1)
    total_calls = sum(r["模型调用(估)"] for r in rows)
    slowest = max(rows, key=lambda r: r["耗时ms"])
    print(f"\n耗时：平均 {avg_ms / 1000:.1f}s/题，最慢 {slowest['id']} {slowest['耗时ms'] / 1000:.1f}s")
    print(f"模型调用：约 {total_calls} 次（估算 = 子问题回答数 + 拆分调用）")
    print(f"top_k: {args.top_k}")
    print(f"\nCSV: {csv_path}")
    print(f"原始记录: {raw_path}")
    print("\n下一步可生成 HTML 报告：.\\\\.venv\\\\Scripts\\\\python.exe scripts\\\\make_report.py")
    sys.exit(2 if errors else 0)


if __name__ == "__main__":
    main()
