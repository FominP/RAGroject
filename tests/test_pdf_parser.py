import pytest

from src.pdf_parser import PDFError, parse_pdf


def test_empty_file_is_rejected() -> None:
    with pytest.raises(PDFError, match="empty"):
        parse_pdf(b"")


def test_non_pdf_file_is_rejected() -> None:
    with pytest.raises(PDFError, match="does not appear"):
        parse_pdf(b"plain text")


def test_oversized_file_is_rejected_before_parsing() -> None:
    with pytest.raises(PDFError, match="larger"):
        parse_pdf(b"%PDF-" + b"0" * 20, max_file_size=10)
