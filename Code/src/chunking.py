"""Page-preserving text chunking for retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .pdf_processor import PageText


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_name: str
    page_number: int
    text: str


def chunk_pages(
    pages: Iterable[PageText],
    document_name: str,
    chunk_size_words: int = 140,
    overlap_words: int = 35,
) -> list[DocumentChunk]:
    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be positive.")
    if overlap_words < 0:
        raise ValueError("overlap_words cannot be negative.")
    if overlap_words >= chunk_size_words:
        raise ValueError("overlap_words must be smaller than chunk_size_words.")

    chunks: list[DocumentChunk] = []
    safe_doc = _slug(document_name)

    for page in pages:
        words = _words(page.text)
        if not words:
            continue

        start = 0
        page_chunk_index = 1
        step = chunk_size_words - overlap_words
        while start < len(words):
            end = min(start + chunk_size_words, len(words))
            chunk_words = words[start:end]
            chunk_id = f"{safe_doc}-p{page.page_number}-c{page_chunk_index}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_name=document_name,
                    page_number=page.page_number,
                    text=" ".join(chunk_words),
                )
            )
            if end == len(words):
                break
            start += step
            page_chunk_index += 1

    return chunks


def _words(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "document"

