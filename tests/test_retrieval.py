from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from src.models import Chunk
from src.retrieval import VectorIndex


class FakeEmbedder:
    def embed_documents(self, texts: Sequence[str]) -> NDArray[np.float32]:
        vectors = {
            "cats": [1.0, 0.0],
            "dogs": [0.0, 1.0],
            "mixed": [0.7, 0.7],
        }
        return np.asarray([vectors[text] for text in texts], dtype=np.float32)

    def embed_query(self, text: str) -> NDArray[np.float32]:
        assert text == "Tell me about dogs"
        return np.asarray([0.0, 1.0], dtype=np.float32)


def make_chunk(chunk_id: str, page: int, text: str) -> Chunk:
    return Chunk(chunk_id=chunk_id, page_number=page, text=text, token_count=1)


def test_search_returns_the_most_similar_chunk_first() -> None:
    chunks = [
        make_chunk("p1-c1", 1, "cats"),
        make_chunk("p2-c1", 2, "dogs"),
        make_chunk("p3-c1", 3, "mixed"),
    ]
    index = VectorIndex.build(chunks, FakeEmbedder())

    results = index.search("Tell me about dogs", top_k=2)

    assert [result.chunk.page_number for result in results] == [2, 3]
    assert results[0].score == 1.0


def test_top_k_is_capped_by_index_size() -> None:
    index = VectorIndex.build(
        [make_chunk("p1-c1", 1, "dogs")],
        FakeEmbedder(),
    )

    assert len(index.search("Tell me about dogs", top_k=10)) == 1
