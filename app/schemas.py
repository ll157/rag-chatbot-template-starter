from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    page: int
    text: str


class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    original_filename: str
    saved_filename: str
    file_path: str
    content_type: Optional[str] = None

    page_count: int
    total_characters: int
    text_preview: str

    chunk_count: int
    chunks_preview: List[DocumentChunk] = Field(default_factory=list)

    embedding_model: str
    embedding_dimension: int
    embedded_chunk_count: int

    vector_db: str
    collection_name: str
    stored_chunk_count: int


class DocumentInfo(BaseModel):
    document_id: str
    original_filename: str
    saved_filename: str
    file_path: str
    content_type: Optional[str] = None
    page_count: int
    total_characters: int
    chunk_count: int
    stored_chunk_count: int
    created_at: str


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentInfo] = Field(default_factory=list)


class DocumentDeleteResponse(BaseModel):
    message: str
    document_id: str
    deleted_file: bool
    deleted_vector_chunks: int


class ChatRequest(BaseModel):
    question: str
    top_k: int = 3


class Source(BaseModel):
    filename: Optional[str] = None
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    page: Optional[int] = None
    text: Optional[str] = None
    distance: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = Field(default_factory=list)
