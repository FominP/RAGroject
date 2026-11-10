from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

import numpy as np
from numpy.typing import NDArray


class Embedder(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> NDArray[np.float32]: ...

    def embed_query(self, text: str) -> NDArray[np.float32]: ...


class FastEmbedder:
    """Small local embedding model backed by ONNX Runtime."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: Sequence[str]) -> NDArray[np.float32]:
        if not texts:
            raise ValueError("At least one document is required for embedding.")
        vectors = list(self._model.embed(list(texts), batch_size=32))
        return np.asarray(vectors, dtype=np.float32)

    def embed_query(self, text: str) -> NDArray[np.float32]:
        if not text.strip():
            raise ValueError("The query cannot be empty.")
        vector = next(iter(self._model.embed([text])))
        return np.asarray(vector, dtype=np.float32)
