from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.embeddings import Embedder
from src.models import Chunk, RetrievedChunk


def _normalize_rows(matrix: NDArray[np.float32]) -> NDArray[np.float32]:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("The embedding model returned an empty vector.")
    return matrix / norms


@dataclass(slots=True)
class VectorIndex:
    chunks: list[Chunk]
    embeddings: NDArray[np.float32]
    embedder: Embedder

    @classmethod
    def build(cls, chunks: list[Chunk], embedder: Embedder) -> VectorIndex:
        if not chunks:
            raise ValueError("At least one chunk is required to build an index.")
        vectors = np.asarray(
            embedder.embed_documents([chunk.text for chunk in chunks]),
            dtype=np.float32,
        )
        if vectors.ndim != 2 or vectors.shape[0] != len(chunks):
            raise ValueError("The embedding model returned an unexpected shape.")
        return cls(chunks=chunks, embeddings=_normalize_rows(vectors), embedder=embedder)

    def search(self, query: str, *, top_k: int = 6) -> list[RetrievedChunk]:
        if not query.strip():
            raise ValueError("The query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        query_vector = np.asarray(self.embedder.embed_query(query), dtype=np.float32)
        if query_vector.ndim != 1 or query_vector.shape[0] != self.embeddings.shape[1]:
            raise ValueError("The query embedding has an unexpected shape.")
        norm = np.linalg.norm(query_vector)
        if norm == 0:
            raise ValueError("The embedding model returned an empty query vector.")

        scores = self.embeddings @ (query_vector / norm)
        result_count = min(top_k, len(self.chunks))
        indices = np.argsort(scores)[::-1][:result_count]
        return [
            RetrievedChunk(chunk=self.chunks[index], score=float(scores[index]))
            for index in indices
        ]
