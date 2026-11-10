from __future__ import annotations

import re

from src.models import Chunk, PageText

DEFAULT_CHUNK_SIZE = 220
DEFAULT_OVERLAP = 40


def _split_words(text: str) -> list[str]:
    """Split text while retaining whitespace for readable reconstruction."""
    return re.findall(r"\S+\s*", text)


def chunk_pages(
    pages: list[PageText],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    step = chunk_size - overlap
    chunks: list[Chunk] = []

    for page in pages:
        words = _split_words(page.text)
        for chunk_number, start in enumerate(range(0, len(words), step), start=1):
            word_slice = words[start : start + chunk_size]
            text = "".join(word_slice).strip()
            if not text:
                continue
            chunks.append(
                Chunk(
                    chunk_id=f"p{page.page_number}-c{chunk_number}",
                    page_number=page.page_number,
                    text=text,
                    token_count=len(word_slice),
                )
            )
            if start + chunk_size >= len(words):
                break

    if not chunks:
        raise ValueError("The document did not produce any searchable passages.")
    return chunks
