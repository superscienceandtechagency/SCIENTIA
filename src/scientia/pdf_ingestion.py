"""Local PDF text extraction into SCIENTIA evidence records."""

import hashlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader

from scientia.evidence import (
    Location,
    Passage,
    Source,
    validate_passage_source,
)

MAX_PASSAGE_LENGTH = 1200
MAX_PDF_BYTES = 64 * 1024 * 1024
MAX_PDF_PAGES = 2_000
MAX_EXTRACTED_TEXT_CHARACTERS = 2_000_000


class PdfIngestionError(Exception):
    """A PDF could not be validated or ingested successfully."""

    def __init__(self, message: str, *, stage: str, page_number: int | None = None):
        super().__init__(message)
        self.stage = stage
        self.page_number = page_number


@dataclass(frozen=True)
class PdfIngestionResult:
    """Source and passages extracted from one local PDF."""

    source: Source
    passages: tuple[Passage, ...]
    original_filename: str


def _split_page_text(text: str) -> tuple[str, ...]:
    remaining = text.strip()
    chunks: list[str] = []
    while remaining:
        if len(remaining) <= MAX_PASSAGE_LENGTH:
            chunks.append(remaining)
            break
        boundary = max(
            (
                index
                for index, character in enumerate(remaining[:MAX_PASSAGE_LENGTH])
                if character.isspace()
            ),
            default=-1,
        )
        if boundary <= 0:
            boundary = MAX_PASSAGE_LENGTH
        chunk = remaining[:boundary].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[boundary:].strip()
    return tuple(chunks)


def ingest_pdf(path: str | Path) -> PdfIngestionResult:
    """Extract a local PDF into source-linked passages with page provenance."""
    if not isinstance(path, (str, Path)):
        raise PdfIngestionError("Input must be a filesystem path", stage="input")
    try:
        pdf_path = Path(path)
    except (TypeError, ValueError, OSError) as exc:
        raise PdfIngestionError(
            "Input must be a valid filesystem path", stage="input"
        ) from exc
    if not pdf_path.is_file():
        raise PdfIngestionError(
            "Input path must refer to an existing regular file", stage="input"
        )
    try:
        with pdf_path.open("rb") as pdf_file:
            original_bytes = pdf_file.read(MAX_PDF_BYTES + 1)
    except OSError as exc:
        raise PdfIngestionError("Could not read input file", stage="read") from exc
    if len(original_bytes) > MAX_PDF_BYTES:
        raise PdfIngestionError(
            "PDF exceeds the configured size limit",
            stage="validate",
        )
    if b"%PDF-" not in original_bytes[:1024]:
        raise PdfIngestionError("Input does not have a PDF header", stage="validate")

    try:
        reader = PdfReader(BytesIO(original_bytes), strict=True)
    except Exception as exc:
        raise PdfIngestionError("Could not parse PDF content", stage="parse") from exc
    if reader.is_encrypted:
        raise PdfIngestionError("Encrypted PDFs are not supported", stage="parse")

    try:
        metadata_title = reader.metadata.title if reader.metadata is not None else None
        page_count = len(reader.pages)
    except Exception as exc:
        raise PdfIngestionError(
            "Could not read PDF metadata or pages", stage="parse"
        ) from exc
    if page_count > MAX_PDF_PAGES:
        raise PdfIngestionError("PDF exceeds the configured page limit", stage="parse")

    filename = pdf_path.name
    title = (
        metadata_title.strip()
        if isinstance(metadata_title, str) and metadata_title.strip()
        else filename
    )
    source = Source(
        source_id=uuid4(),
        title=title,
        content_sha256=hashlib.sha256(original_bytes).hexdigest(),
    )

    passages: list[Passage] = []
    extracted_text_characters = 0
    for page_index in range(page_count):
        page_number = page_index + 1
        try:
            text = reader.pages[page_index].extract_text()
            if text is not None and not isinstance(text, str):
                raise TypeError("PDF page text extraction returned a non-string value")
        except Exception as exc:
            raise PdfIngestionError(
                f"Text extraction failed on page {page_number}",
                stage="extract",
                page_number=page_number,
            ) from exc
        if text is not None:
            extracted_text_characters += len(text)
            if extracted_text_characters > MAX_EXTRACTED_TEXT_CHARACTERS:
                raise PdfIngestionError(
                    "PDF exceeds the configured extracted text limit",
                    stage="extract",
                    page_number=page_number,
                )
        if not text or not text.strip():
            continue
        for chunk in _split_page_text(text):
            passage = Passage(
                passage_id=uuid4(),
                source_id=source.source_id,
                text=chunk,
                location=Location(page_start=page_number, page_end=page_number),
            )
            validate_passage_source(source, passage)
            passages.append(passage)

    if not passages:
        raise PdfIngestionError(
            "PDF produced no extractable text passages", stage="extract"
        )
    return PdfIngestionResult(
        source=source,
        passages=tuple(passages),
        original_filename=filename,
    )
