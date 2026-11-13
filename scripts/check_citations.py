# -*- coding: utf-8 -*-
"""check_citations.py —— 引用真实性对抗校验（给"引用标注"派监考）。

它验证两件事：
  ① 引用真实性：回答里/返回的每个"文件名 第N页"，文件必须真实存在且页码不超范围；
  ② 拒绝能力：故意问库中不存在的型号，系统必须老实说"查不到"，且不得附带假引用。

用法：
    .\\.venv\\Scripts\\python.exe scripts\\check_citations.py

产出：
    docs/eval/测试结果/引用校验_时间戳.json   逐案结果证据

判定原则：
    任何"引用了不存在的文件"或"页码越界"= 违规（VIOLATION）；
    对抗题若没有否定表述 = 违规（疑似编造回答）。
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
RESULT_DIR = ROOT / "docs" / "eval" / "测试结果"
BASE = "http://127.0.0.1:8000"
TIMEOUT = 120

from run_eval import NO_ANSWER_PATTERNS, NO_ANSWER_REGEX  # noqa: E402

# 正常题：验证引用真实（这些题的答案应当带引用）
REAL_QUESTIONS = [
    ("R-01", "A200 的保修期是多久？"),
    ("R-02", "A200 和 Pro 的滤芯仓在哪里？"),
    ("R-03", "滤芯的更换周期是多久？"),
]
# 对抗题：库里没有任何 A300 / X999 的资料，正确行为是"不编造"
ADVERSARIAL_QUESTIONS = [
    ("A-01", "A300 的保修期是多久？"),
    ("A-02", "X999 型号的滤芯多久换一次？"),
]

# 从回答正文里抠 "文件名 第N页" 形式的引用
CITATION_RE = re.compile(r"([^\s；;，,（）()【】\n]{2,60}?)\s*第\s*(\d+)\s*页")


def get_documents() -> dict:
    resp = requests.get(f"{BASE}/api/v1/documents", timeout=15)
    resp.raise_for_status()
    data = resp.json()
    mapping = {}
    for doc in data.get("documents", []):
        page_count = doc.get("page_count") or 0
        for name in (doc.get("original_filename"), doc.get("saved_filename")):
            if name:
                mapping[name] = page_count
    return mapping


def has_negation(text: str) -> bool:
    if any(p in text for p in NO_ANSWER_PATTERNS):
        return True
    return any(re.search(rx, text) for rx in NO_ANSWER_REGEX)


def validate_citations(answer: str, sources: list, doc_pages: dict) -> list:
    """逐条核对引用，返回问题清单（空 = 全部真实）。"""
    problems = []

    for src in sources:
        filename = src.get("filename")
        page = src.get("page")
        if filename not in doc_pages:
            problems.append(f"引用了清单中不存在的文件：{filename}")
            continue
        if page is None:
            problems.append(f"{filename} 的引用缺少页码")
        elif not (1 <= int(page) <= max(doc_pages[filename], 1)):
            problems.append(f"{filename} 页码越界：第{page}页（共{doc_pages[filename]}页）")

    for m in CITATION_RE.finditer(answer):
        filename, page = m.group(1).strip(), int(m.group(2))
        matched = [name for name in doc_pages if name == filename or filename.endswith(name)]
        if not matched:
            problems.append(f"正文引用了不存在的文件：{filename}")
            continue
        page_count = doc_pages[matched[0]]
        if not (1 <= page <= max(page_count, 1)):
            problems.append(f"正文 {filename} 页码越界：第{page}页（共{page_count}页）")

    return problems


def main() -> None:
    try:
        requests.get(f"{BASE}/health", timeout=5).raise_for_status()
    except Exception as exc:
        print(f"[前置失败] 服务未就绪: {exc}")
        sys.exit(1)

    doc_pages = get_documents()
    print(f"知识库登记 {len(doc_pages)} 个文件名，开始引用校验...\n")

    cases = []
    violations = 0

    for tag, question in REAL_QUESTIONS:
        data = requests.post(
            f"{BASE}/api/v1/chat",
            json={"question": question, "top_k": 4},
            timeout=TIMEOUT,
        ).json()
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        problems = validate_citations(answer, sources, doc_pages)
        cited = bool(sources) or bool(CITATION_RE.search(answer))
        status = "VIOLATION" if problems else ("PASS" if cited else "NO_CITATION")
        violations += 1 if problems else 0
        print(f"[{tag}] {status:12s} 引用 {len(sources)} 条 | {question}")
        for p in problems:
            print(f"        ⚠ {p}")
        cases.append({
            "tag": tag, "type": "real", "question": question, "status": status,
            "problems": problems, "source_count": len(sources),
            "answer": answer[:400],
            "sources": [{"filename": s.get("filename"), "page": s.get("page")} for s in sources],
        })
        time.sleep(1)

    for tag, question in ADVERSARIAL_QUESTIONS:
        data = requests.post(
            f"{BASE}/api/v1/chat",
            json={"question": question, "top_k": 4},
            timeout=TIMEOUT,
        ).json()
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        problems = validate_citations(answer, sources, doc_pages)
        if not has_negation(answer):
            problems.append("对抗题未见否定表述（疑似编造回答）")
        status = "VIOLATION" if problems else "REFUSED_OK"
        violations += 1 if problems else 0
        print(f"[{tag}] {status:12s} 对抗题（库中无此型号）| {question}")
        for p in problems:
            print(f"        ⚠ {p}")
        cases.append({
            "tag": tag, "type": "adversarial", "question": question, "status": status,
            "problems": problems, "source_count": len(sources),
            "answer": answer[:400],
            "sources": [{"filename": s.get("filename"), "page": s.get("page")} for s in sources],
        })
        time.sleep(1)

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / f"引用校验_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    out.write_text(json.dumps({
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "document_files": len(doc_pages),
        "violations": violations,
        "cases": cases,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n===== 引用校验汇总 =====")
    print(f"案例 {len(cases)} 个，违规 {violations} 个")
    print(f"证据：{out}")
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
