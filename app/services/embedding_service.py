from functools import lru_cache
from typing import List
from app.config import settings

from sentence_transformers import SentenceTransformer



@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    model = SentenceTransformer(settings.embedding_model)
    return model


def create_embedding(text: str) -> list[float]:
    if not text.strip():
        raise ValueError("Text is required for embedding")

    model = get_embedding_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True,
    )

    return embedding.tolist()


def create_embeddings_for_chunks(chunks: List[dict]) -> List[dict]:
    if not chunks:
        return []

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
    )

    embedded_chunks = []

    for chunk, embedding in zip(chunks, embeddings):
        embedded_chunks.append(
            {
                **chunk,
                "embedding": embedding.tolist(),
            }
        )

    return embedded_chunks


def get_embedding_dimension(embedded_chunks: List[dict]) -> int:
    if not embedded_chunks:
        return 0

    first_embedding = embedded_chunks[0].get("embedding", [])

    return len(first_embedding)