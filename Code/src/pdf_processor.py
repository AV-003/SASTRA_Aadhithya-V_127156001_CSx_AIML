"""PDF extraction utilities with graceful fallbacks.

PyMuPDF is the preferred extractor. A tiny basic parser is included only so the
synthetic sample and tests remain usable when PyMuPDF is not installed. The
basic parser is intentionally limited and is not a replacement for PyMuPDF or
OCR.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable


class PdfProcessingError(ValueError):
    """Raised when a PDF cannot be processed into useful page text."""


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class DocumentExtractionResult:
    document_name: str
    page_count: int
    pages: list[PageText]
    warnings: list[str]
    extractor: str
    document_id: str

    @property
    def text_preview(self) -> str:
        combined = "\n\n".join(page.text for page in self.pages if page.text.strip())
        return combined[:1200]

    @property
    def extracted_character_count(self) -> int:
        return sum(len(page.text) for page in self.pages)


def extract_pdf_path(path: str | Path) -> DocumentExtractionResult:
    pdf_path = Path(path)
    return extract_pdf_bytes(pdf_path.read_bytes(), pdf_path.name)


def extract_pdf_bytes(file_bytes: bytes, document_name: str) -> DocumentExtractionResult:
    if not file_bytes:
        raise PdfProcessingError("The uploaded file is empty.")
    if not document_name.lower().endswith(".pdf"):
        raise PdfProcessingError("Unsupported file type. Please upload a PDF file.")
    if not file_bytes.lstrip().startswith(b"%PDF"):
        raise PdfProcessingError("The file does not appear to be a valid PDF.")

    document_id = sha256(document_name.encode("utf-8") + file_bytes).hexdigest()[:16]
    pymupdf_error = None

    try:
        return _extract_with_pymupdf(file_bytes, document_name, document_id)
    except ImportError as exc:
        pymupdf_error = str(exc)
    except Exception as exc:  # Corrupted PDFs commonly fail here.
        pymupdf_error = f"PyMuPDF could not read this PDF: {exc}"

    fallback = _extract_with_basic_parser(file_bytes, document_name, document_id)
    if fallback.extracted_character_count > 0:
        warnings = list(fallback.warnings)
        warnings.append(
            "PyMuPDF is unavailable or failed, so a limited built-in parser was used. "
            "Install PyMuPDF for reliable extraction from real HLD PDFs."
        )
        if pymupdf_error:
            warnings.append(pymupdf_error)
        return DocumentExtractionResult(
            document_name=fallback.document_name,
            page_count=fallback.page_count,
            pages=fallback.pages,
            warnings=warnings,
            extractor=fallback.extractor,
            document_id=fallback.document_id,
        )

    details = f" Details: {pymupdf_error}" if pymupdf_error else ""
    raise PdfProcessingError(
        "No extractable text was found. The PDF may be scanned, image-only, "
        "encrypted, or corrupted. OCR is not bundled with this prototype."
        + details
    )


def _extract_with_pymupdf(
    file_bytes: bytes, document_name: str, document_id: str
) -> DocumentExtractionResult:
    try:
        import pymupdf as fitz  # type: ignore
    except ImportError:
        try:
            import fitz  # type: ignore
        except ImportError as exc:
            raise ImportError("PyMuPDF is not installed.") from exc

    warnings: list[str] = []
    pages: list[PageText] = []

    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        if doc.is_encrypted:
            raise PdfProcessingError("Encrypted PDFs are not supported by this prototype.")
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            normalized = _normalize_text(text)
            if not normalized:
                warnings.append(
                    f"Page {index} has no extractable text. It may be scanned or blank."
                )
            pages.append(PageText(page_number=index, text=normalized))
        page_count = doc.page_count

    if not any(page.text for page in pages):
        warnings.append("OCR is not available in this prototype.")

    return DocumentExtractionResult(
        document_name=document_name,
        page_count=page_count,
        pages=pages,
        warnings=warnings,
        extractor="PyMuPDF",
        document_id=document_id,
    )


def _extract_with_basic_parser(
    file_bytes: bytes, document_name: str, document_id: str
) -> DocumentExtractionResult:
    warnings = [
        "Using basic PDF text fallback. This only supports simple, uncompressed text streams."
    ]
    page_count = _count_pdf_pages(file_bytes)
    streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", file_bytes, flags=re.S)
    pages: list[PageText] = []

    for stream in streams:
        text = _extract_literal_text_from_stream(stream)
        if text:
            pages.append(PageText(page_number=len(pages) + 1, text=_normalize_text(text)))

    if not pages and page_count:
        pages = [PageText(page_number=index, text="") for index in range(1, page_count + 1)]

    if page_count == 0:
        page_count = len(pages)
    if page_count and len(pages) < page_count:
        existing = {page.page_number for page in pages}
        for page_number in range(1, page_count + 1):
            if page_number not in existing:
                pages.append(PageText(page_number=page_number, text=""))
        pages.sort(key=lambda page: page.page_number)

    for page in pages:
        if not page.text:
            warnings.append(f"Page {page.page_number} has no extractable text.")

    return DocumentExtractionResult(
        document_name=document_name,
        page_count=page_count or len(pages),
        pages=pages,
        warnings=warnings,
        extractor="basic-pdf-fallback",
        document_id=document_id,
    )


def _count_pdf_pages(file_bytes: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", file_bytes))


def _extract_literal_text_from_stream(stream: bytes) -> str:
    decoded = stream.decode("latin-1", errors="ignore")
    if "BT" not in decoded or "ET" not in decoded:
        return ""

    pieces: list[str] = []
    for match in re.finditer(r"\(((?:\\.|[^\\()])*)\)", decoded, flags=re.S):
        pieces.append(_decode_pdf_literal(match.group(1)))
    return "\n".join(piece for piece in pieces if piece.strip())


def _decode_pdf_literal(value: str) -> str:
    def replace_octal(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 8))

    value = re.sub(r"\\([0-7]{1,3})", replace_octal, value)
    replacements = {
        r"\n": "\n",
        r"\r": "\n",
        r"\t": "\t",
        r"\b": "\b",
        r"\f": "\f",
        r"\(": "(",
        r"\)": ")",
        r"\\": "\\",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value


def _normalize_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\x00", "").splitlines()]
    clean_lines = [line for line in lines if line]
    return "\n".join(clean_lines).strip()


def pages_from_strings(page_texts: Iterable[str]) -> list[PageText]:
    return [
        PageText(page_number=index, text=_normalize_text(text))
        for index, text in enumerate(page_texts, start=1)
    ]
