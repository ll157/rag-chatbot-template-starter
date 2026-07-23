from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas import (
    DocumentDeleteResponse,
    DocumentInfo,
    DocumentListResponse,
)
from app.services.document_service import (
    delete_document_metadata,
    get_document_by_id,
    list_documents,
)
from app.services.vector_service import delete_document_from_vector_store

router = APIRouter()


@router.get("", response_model=DocumentListResponse)
async def get_documents():
    documents = list_documents()

    return DocumentListResponse(
        total=len(documents),
        documents=[
            DocumentInfo(**document)
            for document in documents
        ],
    )


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    document = get_document_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return DocumentInfo(**document)


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    document = get_document_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    deleted_vector_chunks = delete_document_from_vector_store(
        document_id=document_id,
    )

    file_path = Path(document["file_path"])
    deleted_file = False

    if file_path.exists():
        file_path.unlink()
        deleted_file = True

    delete_document_metadata(
        document_id=document_id,
    )

    return DocumentDeleteResponse(
        message="Document deleted successfully",
        document_id=document_id,
        deleted_file=deleted_file,
        deleted_vector_chunks=deleted_vector_chunks,
    )