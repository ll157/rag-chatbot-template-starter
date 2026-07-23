from typing import List


def split_text_with_overlap(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - chunk_overlap

    return chunks


def create_chunks_from_pages(
    pages: list[dict],
    document_id: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:
    all_chunks = []

    for page in pages:
        page_number = page["page"]
        page_text = page["text"]

        page_chunks = split_text_with_overlap(
            text=page_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for index, chunk_text in enumerate(page_chunks, start=1):
            chunk_id = f"{document_id}-page-{page_number}-chunk-{index}"

            all_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "page": page_number,
                    "text": chunk_text,
                }
            )

    return all_chunks