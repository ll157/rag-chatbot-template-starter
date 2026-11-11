from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse, Source
from app.services.chat_service import generate_answer
from app.services.embedding_service import create_embedding
from app.services.query_planning_service import (
    build_citation,
    merge_sources,
    needs_splitting,
    split_question,
)
from app.services.vector_service import search_similar_chunks

router = APIRouter()


def _to_sources(chunks: List[dict]) -> List[Source]:
    return [
        Source(
            filename=chunk.get("filename"),
            document_id=chunk.get("document_id"),
            chunk_id=chunk.get("chunk_id"),
            page=chunk.get("page"),
            text=chunk.get("text"),
            distance=chunk.get("distance"),
        )
        for chunk in chunks
    ]


@router.post("", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    try:
        question = request.question.strip()
        if not question:
            raise ValueError("Question is required")

        # ---- Day5 新增：子问题拆分（规则先行，规则命中才调模型） ----
        sub_questions = [question]
        if needs_splitting(question):
            sub_questions = split_question(question)

        single = len(sub_questions) == 1

        # ---- 逐个子问题：检索 → 回答 → 程序自动标注引用 ----
        sections = []
        all_chunks: List[List[dict]] = []

        for index, sub in enumerate(sub_questions, start=1):
            query_embedding = create_embedding(text=sub)
            chunks = search_similar_chunks(
                query_embedding=query_embedding,
                top_k=request.top_k,
            )
            all_chunks.append(chunks)

            if not chunks:
                sections.append(f"【子问题 {index}】{sub}\n→ 未在资料中找到相关信息。")
                continue

            answer = generate_answer(question=sub, sources=chunks)

            if single:
                # 单问题：保持旧行为（不加包装），兼容评测脚本与旧调用方
                return ChatResponse(
                    answer=answer,
                    sources=_to_sources(chunks),
                    sub_questions=[],
                )

            citation = build_citation(chunks)
            citation_note = f"\n（依据：{citation}）" if citation else ""
            sections.append(
                f"【子问题 {index}】{sub}\n{answer}{citation_note}"
            )

        merged = merge_sources(all_chunks)

        if not merged:
            return ChatResponse(
                answer=(
                    "No relevant information was found. "
                    "Upload a PDF first, or try rephrasing your question."
                ),
                sources=[],
                sub_questions=[] if single else sub_questions,
            )

        final_answer = (
            f"你的问题包含 {len(sub_questions)} 个子问题，逐一回答如下：\n\n"
            + "\n\n".join(sections)
        )

        return ChatResponse(
            answer=final_answer,
            sources=_to_sources(merged),
            sub_questions=sub_questions,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        print(f"Chat error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer from document chunks",
        )
