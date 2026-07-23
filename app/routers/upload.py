from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.schemas import DocumentChunk, DocumentUploadResponse
from app.services.chunk_service import create_chunks_from_pages
from app.services.document_service import save_document_metadata
from app.services.embedding_service import (
    create_embeddings_for_chunks,
    get_embedding_dimension,
)
from app.services.pdf_service import (
    build_text_preview,
    extract_text_from_pdf,
    save_pdf_file,
)
from app.services.vector_service import COLLECTION_NAME, add_chunks_to_vector_store

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    try:
        saved_file = await save_pdf_file(file=file, upload_dir=settings.upload_dir)

        pages = extract_text_from_pdf(saved_file["file_path"])
        total_characters = sum(len(page["text"]) for page in pages)
        text_preview = build_text_preview(pages=pages, max_length=500)

        chunks = create_chunks_from_pages(
            pages=pages,
            document_id=saved_file["document_id"],
            chunk_size=1000,
            chunk_overlap=200,
        )

        embedded_chunks = create_embeddings_for_chunks(chunks=chunks)
        embedding_dimension = get_embedding_dimension(embedded_chunks=embedded_chunks)

        stored_chunk_count = add_chunks_to_vector_store(
            embedded_chunks=embedded_chunks,
            original_filename=saved_file["original_filename"],
        )

        save_document_metadata(
            document_id=saved_file["document_id"],
            original_filename=saved_file["original_filename"],
            saved_filename=saved_file["saved_filename"],
            file_path=saved_file["file_path"],
            content_type=saved_file["content_type"],
            page_count=len(pages),
            total_characters=total_characters,
            chunk_count=len(chunks),
            stored_chunk_count=stored_chunk_count,
        )

        chunks_preview = [
            DocumentChunk(
                chunk_id=chunk["chunk_id"],
                document_id=chunk["document_id"],
                page=chunk["page"],
                text=chunk["text"],
            )
            for chunk in chunks[:3]
        ]

        return DocumentUploadResponse(
            message="PDF uploaded, embedded, and stored in ChromaDB successfully",
            document_id=saved_file["document_id"],
            original_filename=saved_file["original_filename"],
            saved_filename=saved_file["saved_filename"],
            file_path=saved_file["file_path"],
            content_type=saved_file["content_type"],
            page_count=len(pages),
            total_characters=total_characters,
            text_preview=text_preview,
            chunk_count=len(chunks),
            chunks_preview=chunks_preview,
            embedding_model=settings.embedding_model,
            embedding_dimension=embedding_dimension,
            embedded_chunk_count=len(embedded_chunks),
            vector_db="ChromaDB",
            collection_name=COLLECTION_NAME,
            stored_chunk_count=stored_chunk_count,
        )

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        print(f"Upload error: {error}")
        raise HTTPException(status_code=500, detail="Failed to process the PDF")
