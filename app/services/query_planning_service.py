# -*- coding: utf-8 -*-
"""Day5 新增：子问题拆分服务（查询规划）。

三道防线判断是否需要拆分：
1. 标点规则（问号/分号 >= 2）
2. 疑问词计数（>= 2 个不同疑问词）
3. 都没拦住 → 按单问题处理（诚实漏过，模型兜底留给后续迭代）

拆分本身用一次受约束的模型调用（只允许输出 JSON 数组，最多 3 项），
失败自动回退为"不拆分"——规划失败不能挡住正常问答。
"""
import json
import re
from typing import List

from openai import OpenAI

from app.config import settings

# 疑问词表：出现 2 个及以上视为复合问题（应对"说话不加标点"的场景）
QUESTION_WORDS = [
    "多少", "怎么", "怎样", "如何", "什么", "哪些", "哪个",
    "多久", "是否", "为什么", "为啥", "几", "吗",
]

SPLIT_PROMPT = """你是问题拆分器。把用户的复合问题拆成独立的子问题，规则：
1. 最多拆成 3 个子问题
2. 每个子问题必须能独立回答，不要改写原意
3. 简单问题（只有一个疑问点）直接返回只含原问题的数组
4. 只输出 JSON 数组，禁止输出任何解释文字

示例：
输入：A200保修多久？滤芯多久换？
输出：["A200 的保修期是多久？", "A200 的滤芯多久更换一次？"]

用户问题：{question}"""


def needs_splitting(question: str) -> bool:
    """三道防线中的前两道：纯规则判断，零成本。"""
    # 防线 1：标点
    if len(re.findall(r"[？?；;]", question)) >= 2:
        return True
    # 防线 2：疑问词出现次数（同一疑问词出现 2 次也算——应对"不加标点"的口语）
    # 例："保修多久滤芯多久换"（无标点）→ "多久"出现 2 次 → 拆分
    hits = sum(question.count(word) for word in QUESTION_WORDS)
    return hits >= 2


def split_question(question: str) -> List[str]:
    """防线 2 命中后，用一次受约束的模型调用完成拆分。失败回退为原问题。"""
    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=settings.deepseek_timeout_seconds,
    )
    prompt = SPLIT_PROMPT.format(question=question)

    # 手动重试 2 次：网络抖动不该让整个问答失败
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200,
            )
            text = (response.choices[0].message.content or "").strip()
            sub_questions = _parse_json_list(text)
            if sub_questions:
                return sub_questions[:3]
        except Exception as exc:
            print(f"[split_question] attempt {attempt + 1} failed: {exc}")

    return [question]


def _parse_json_list(text: str) -> List[str]:
    """从模型输出里稳健地抠出 JSON 数组（容忍代码围栏和废话）。"""
    match = re.search(r"\[.*\]", text, re.S)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [str(item).strip() for item in data if str(item).strip()]


def build_citation(chunks: List[dict], max_refs: int = 2) -> str:
    """程序自动生成引用标注（不花模型钱）：文件名 + 页码，去重。"""
    seen = set()
    parts = []
    for chunk in chunks:
        filename = chunk.get("filename")
        if not filename:
            continue
        key = (filename, chunk.get("page"))
        if key in seen:
            continue
        seen.add(key)
        page = chunk.get("page")
        parts.append(f"{filename} 第{page}页" if page is not None else filename)
        if len(parts) >= max_refs:
            break
    return "；".join(parts)


def merge_sources(all_chunks: List[List[dict]]) -> List[dict]:
    """合并多个子问题的检索结果，按 chunk_id 去重，保持顺序。"""
    merged = []
    seen_ids = set()
    for chunks in all_chunks:
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id")
            if chunk_id in seen_ids:
                continue
            seen_ids.add(chunk_id)
            merged.append(chunk)
    return merged
