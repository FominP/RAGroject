from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from src.models import PageText

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_PAGES = 100


class PDFError(ValueError):
    """Raised when a PDF cannot be safely processed."""


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\x00", "").splitlines()]
    return "\n".join(line for line in lines if line).strip()


def parse_pdf(
    data: bytes,
    *,
    max_file_size: int = MAX_FILE_SIZE_BYTES,
    max_pages: int = MAX_PAGES,
) -> list[PageText]:
    if not data:
        raise PDFError("The uploaded file is empty.")
    if len(data) > max_file_size:
        raise PDFError(f"The PDF is larger than {max_file_size // (1024 * 1024)} MB.")
    if not data.lstrip().startswith(b"%PDF-"):
        raise PDFError("The uploaded file does not appear to be a PDF.")

    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise PDFError("Password-protected PDFs are not supported.")
        if len(reader.pages) > max_pages:
            raise PDFError(f"The PDF has more than {max_pages} pages.")

        pages: list[PageText] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = _clean_text(page.extract_text() or "")
            if text:
                pages.append(PageText(page_number=page_number, text=text))
    except PDFError:
        raise
    except (PdfReadError, ValueError, OSError) as exc:
        raise PDFError("The PDF is damaged or could not be parsed.") from exc

    if not pages:
        raise PDFError(
            "No selectable text was found. Scanned PDFs require OCR, which is "
            "not enabled in this demo."
        )
    return pages
