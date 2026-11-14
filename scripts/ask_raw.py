# -*- coding: utf-8 -*-
"""ask_raw.py —— 裸大模型对照组（不查知识库，直接问 DeepSeek）。

用途：Day7 普通搜索对照实验。同样的 6 道题，裸模型答一遍、知识库版答一遍，
对比谁准谁编——量化"知识库带来的净增量"。

用法：
    .\\.venv\\Scripts\\python.exe scripts\\ask_raw.py

操作：脚本逐题出题，你用手机秒表计时（按回车出题 → 答案出现即停表），
把你记的秒数和"你觉得它答得靠不靠谱"记进对照表。
脚本自己也会记录接口耗时作为备份证据（存 docs/eval/测试结果/裸模型对照_时间戳.json）。
"""

import io
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from openai import OpenAI  # noqa: E402

from app.config import settings  # noqa: E402

# 与 RAG 侧完全相同的 6 道对照题（顺序也一致）
QUESTIONS = [
    "A200 零件坏了保修吗？要另外花钱吗？",
    "有七天无理由退货吗？",
    "宣传页说 A200 整机保修 36 个月，这个说法对吗？",
    # 2026-11-14 修正：原稿误加"净水器"（语料是空气净化器，且用户原题无此词），导致对照两边题目不一致，该组数据作废
    "推荐一个家用的吧，我们家三个人。",
    "A200 的滤芯多久换一次？",
    "A200 和 A200 Pro 的滤芯通用吗？",
]

RESULT_DIR = ROOT / "docs" / "eval" / "测试结果"


def main() -> None:
    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=settings.deepseek_timeout_seconds,
        max_retries=2,
    )

    print("=" * 60)
    print("裸大模型对照组（不查知识库）")
    print("每题：按回车出题 → 答案出现时按停手机秒表 → 记录")
    print("=" * 60)

    records = []
    only = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 可传题号只跑单题，如：ask_raw.py 4
    for i, question in enumerate(QUESTIONS, 1):
        if only and i != only:
            continue
        input(f"\n[{i}/{len(QUESTIONS)}] 手机秒表归零，按回车提问：{question}")
        started = time.time()
        resp = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[{"role": "user", "content": question}],
            temperature=0.1,
        )
        elapsed = time.time() - started
        answer = resp.choices[0].message.content or ""
        print(f"\n----- 裸模型回答（接口耗时 {elapsed:.1f}s）-----")
        print(answer.strip()[:600])
        print("----------------------------------------")
        records.append({
            "index": i, "question": question,
            "api_elapsed_s": round(elapsed, 1),
            "answer": answer.strip(),
        })

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / f"裸模型对照_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    out.write_text(json.dumps({
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "raw_llm_no_retrieval",
        "records": records,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n证据已存：{out}")
    print("现在把你记的秒数和判断填进对照表发给教练。")


if __name__ == "__main__":
    main()
