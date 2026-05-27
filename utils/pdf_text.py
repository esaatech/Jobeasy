"""Extract plain text from PDF files."""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

PathLike = str | Path


class PdfTextExtractionError(Exception):
    """Raised when a PDF cannot be read or yields no extractable text."""


def extract_text_from_pdf(source: PathLike | BinaryIO | bytes) -> str:
    """
    Extract all text from a PDF, concatenating pages in order.

    Args:
        source: Filesystem path, path-like string, bytes, or a binary file object
            opened for reading (e.g. uploaded file, ``BytesIO``).

    Returns:
        Extracted text with a newline after each page's content.

    Raises:
        PdfTextExtractionError: If the PDF cannot be opened or contains no text.
    """
    if isinstance(source, bytes):
        return _extract_from_file_object(io.BytesIO(source))

    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            raise PdfTextExtractionError(f"PDF file not found: {path}")
        return _extract_from_path(path)

    if hasattr(source, "read"):
        return _extract_from_file_object(source)

    raise PdfTextExtractionError(
        f"Unsupported PDF source type: {type(source).__name__}"
    )


def _extract_from_path(path: Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        return _extract_with_pypdf2_path(path)

    try:
        text = _extract_with_pdfplumber_path(path)
    except Exception as exc:
        raise PdfTextExtractionError(f"Failed to read PDF: {path}") from exc

    return _validate_non_empty(text, path)


def _extract_from_file_object(fp: BinaryIO) -> str:
    try:
        import pdfplumber
    except ImportError:
        return _extract_with_pypdf2_file_object(fp)

    if hasattr(fp, "seek"):
        fp.seek(0)

    try:
        text = _extract_with_pdfplumber_file_object(fp)
    except Exception as exc:
        raise PdfTextExtractionError("Failed to read PDF from file object") from exc

    return _validate_non_empty(text, "uploaded PDF")


def _extract_with_pdfplumber_path(path: Path) -> str:
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        return _join_pages(pdf.pages)


def _extract_with_pdfplumber_file_object(fp: BinaryIO) -> str:
    import pdfplumber

    with pdfplumber.open(fp) as pdf:
        return _join_pages(pdf.pages)


def _extract_with_pypdf2_path(path: Path) -> str:
    import PyPDF2

    with path.open("rb") as file:
        return _extract_with_pypdf2_reader(PyPDF2.PdfReader(file))


def _extract_with_pypdf2_file_object(fp: BinaryIO) -> str:
    import PyPDF2

    if hasattr(fp, "seek"):
        fp.seek(0)
    return _extract_with_pypdf2_reader(PyPDF2.PdfReader(fp))


def _extract_with_pypdf2_reader(reader) -> str:
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return _join_page_texts(parts)


def _join_pages(pages) -> str:
    return _join_page_texts(page.extract_text() or "" for page in pages)


def _join_page_texts(parts) -> str:
    return "\n".join(part for part in parts if part is not None)


def _validate_non_empty(text: str, source_label) -> str:
    if not text.strip():
        raise PdfTextExtractionError(
            f"No extractable text found in PDF ({source_label}). "
            "The file may be scanned images without a text layer."
        )
    return text
