from src.chunking import _split_words, chunk_pages
from src.models import PageText


def test_chunking_preserves_page_numbers_and_overlap() -> None:
    text = " ".join(f"token-{number}" for number in range(120))
    page = PageText(page_number=7, text=text)

    chunks = chunk_pages([page], chunk_size=40, overlap=10)

    assert len(chunks) > 1
    assert all(chunk.page_number == 7 for chunk in chunks)
    assert chunks[0].chunk_id == "p7-c1"

    first_words = [word.strip() for word in _split_words(chunks[0].text)]
    second_words = [word.strip() for word in _split_words(chunks[1].text)]
    assert first_words[-10:] == second_words[:10]


def test_short_pages_create_one_chunk_each() -> None:
    pages = [
        PageText(page_number=1, text="First page"),
        PageText(page_number=3, text="Third page"),
    ]

    chunks = chunk_pages(pages, chunk_size=50, overlap=5)

    assert [chunk.page_number for chunk in chunks] == [1, 3]


def test_invalid_overlap_is_rejected() -> None:
    page = PageText(page_number=1, text="content")

    try:
        chunk_pages([page], chunk_size=10, overlap=10)
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("Expected invalid overlap to raise ValueError")
