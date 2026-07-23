from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse, Source
from app.services.chat_service import generate_answer
from app.services.embedding_service import create_embedding
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
        if not request.question.strip():
            raise ValueError("Question is required")

        query_embedding = create_embedding(text=request.question)
        chunks = search_similar_chunks(
            query_embedding=query_embedding,
            top_k=request.top_k,
        )

        if not chunks:
            return ChatResponse(
                answer=(
                    "No relevant information was found. "
                    "Upload a PDF first, or try rephrasing your question."
                ),
                sources=[],
            )

        answer = generate_answer(question=request.question, sources=chunks)

        return ChatResponse(answer=answer, sources=_to_sources(chunks))

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        print(f"Chat error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer from document chunks",
        )
