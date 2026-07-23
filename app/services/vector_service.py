from typing import List

import chromadb

from app.config import settings


COLLECTION_NAME = "documents"


def get_chroma_client():
    client = chromadb.PersistentClient(
        path=settings.chroma_dir,
    )

    return client


def get_document_collection():
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Document chunks for RAG chatbot",
        },
    )

    return collection


def add_chunks_to_vector_store(
    embedded_chunks: List[dict],
    original_filename: str,
) -> int:
    if not embedded_chunks:
        return 0

    collection = get_document_collection()

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for chunk in embedded_chunks:
        ids.append(chunk["chunk_id"])
        documents.append(chunk["text"])
        embeddings.append(chunk["embedding"])

        metadatas.append(
            {
                "document_id": chunk["document_id"],
                "chunk_id": chunk["chunk_id"],
                "page": chunk["page"],
                "filename": original_filename,
            }
        )

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(ids)


def search_similar_chunks(
    query_embedding: list[float],
    top_k: int = 3,
    document_id: str | None = None,
) -> list[dict]:
    collection = get_document_collection()

    where = {"document_id": document_id} if document_id else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    chunks = []

    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None
        chunk_id = ids[index] if index < len(ids) else metadata.get("chunk_id")

        chunks.append(
            {
                "chunk_id": chunk_id,
                "document_id": metadata.get("document_id"),
                "filename": metadata.get("filename"),
                "page": metadata.get("page"),
                "text": document,
                "distance": distance,
            }
        )

    return chunks


def delete_document_from_vector_store(document_id: str) -> int:
    collection = get_document_collection()

    results = collection.get(
        where={
            "document_id": document_id,
        }
    )

    ids = results.get("ids", [])

    if not ids:
        return 0

    collection.delete(
        ids=ids,
    )

    return len(ids)