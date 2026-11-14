from typing import List

from openai import OpenAI

from app.config import settings
from app.services.llm.prompt import build_context_from_sources, build_rag_prompt


class DeepSeekProvider:
    """DeepSeek provider via OpenAI-compatible Chat Completions API.

    DeepSeek does not support the OpenAI Responses API used by
    OpenAIProvider, so this provider calls chat.completions instead.
    """

    def __init__(self):
        if not settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek")
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=settings.deepseek_timeout_seconds,
        )

    def generate(self, question: str, sources: List[dict]) -> str:
        context = build_context_from_sources(sources, settings.llm_max_context_chars)
        if not context.strip():
            return "未在资料中找到与该问题相关的信息。"
        prompt = build_rag_prompt(question=question, context=context)

        # 2026-11-14 加固：独立测试 T-01 发现模型偶发返回空内容且被透传给用户
        # （检索正常、耗时正常、answer 为空字符串）。防线：空内容自动重试 1 次，
        # 仍为空则返回兜底话术——绝不让用户看到"空白回答"。
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = self.client.chat.completions.create(
                    model=settings.deepseek_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=settings.deepseek_max_tokens,
                    temperature=0.1,
                )
            except Exception as exc:
                last_error = exc
                if attempt == 1:
                    detail = str(exc)[:200]
                    raise RuntimeError(f"DeepSeek generation failed: {detail}") from exc
                continue
            content = (response.choices[0].message.content or "").strip()
            if content:
                return content
            # 空内容：重试一次（偶发的模型侧异常，重试通常可恢复）
        return "抱歉，本次回答生成失败，请重新提问。"
