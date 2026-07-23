import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def save_pdf_file(file: UploadFile, upload_dir: str) -> dict:
    if not file.filename:
        raise ValueError("Filename is required")

    if not file.filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported")

    document_id = str(uuid4())
    saved_filename = f"{document_id}.pdf"

    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    saved_path = upload_path / saved_filename

    with saved_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    await file.close()

    return {
        "document_id": document_id,
        "original_filename": Path(file.filename).name,
        "saved_filename": saved_filename,
        "file_path": str(saved_path),
        "content_type": file.content_type,
    }


def extract_text_from_pdf(file_path: str) -> list[dict]:
    from pypdf import PdfReader

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    reader = PdfReader(str(path))

    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        pages.append({"page": page_number, "text": text})

    return pages


def build_text_preview(pages: list[dict], max_length: int = 500) -> str:
    combined = " ".join(page["text"] for page in pages if page.get("text"))
    combined = combined.strip()
    if len(combined) <= max_length:
        return combined
    return combined[:max_length] + "..."
