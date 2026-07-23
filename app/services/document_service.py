import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import settings


def _get_metadata_path() -> Path:
    path = Path(settings.documents_metadata_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_documents() -> list[dict]:
    path = _get_metadata_path()

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            return []

    if not isinstance(data, list):
        return []

    return data


def _write_documents(documents: list[dict]) -> None:
    path = _get_metadata_path()

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2,
        )


def save_document_metadata(
    document_id: str,
    original_filename: str,
    saved_filename: str,
    file_path: str,
    content_type: Optional[str],
    page_count: int,
    total_characters: int,
    chunk_count: int,
    stored_chunk_count: int,
    ocr_page_count: int = 0,
) -> dict:
    documents = _read_documents()

    document = {
        "document_id": document_id,
        "original_filename": original_filename,
        "saved_filename": saved_filename,
        "file_path": file_path,
        "content_type": content_type,
        "page_count": page_count,
        "total_characters": total_characters,
        "chunk_count": chunk_count,
        "stored_chunk_count": stored_chunk_count,
        "ocr_page_count": ocr_page_count,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    documents = [
        item
        for item in documents
        if item.get("document_id") != document_id
    ]

    documents.append(document)

    _write_documents(documents)

    return document


def list_documents() -> list[dict]:
    documents = _read_documents()

    return sorted(
        documents,
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )


def get_document_by_id(document_id: str) -> Optional[dict]:
    documents = _read_documents()

    for document in documents:
        if document.get("document_id") == document_id:
            return document

    return None


def delete_document_metadata(document_id: str) -> bool:
    documents = _read_documents()

    remaining_documents = [
        document
        for document in documents
        if document.get("document_id") != document_id
    ]

    if len(remaining_documents) == len(documents):
        return False

    _write_documents(remaining_documents)

    return True