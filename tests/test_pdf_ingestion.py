import hashlib
from io import BytesIO

import pytest
from pypdf import PdfWriter

import scientia.pdf_ingestion as pdf_ingestion
from scientia.evidence import Location, validate_passage_source
from scientia.pdf_ingestion import PdfIngestionError, ingest_pdf


def _pdf_bytes(pages: list[str], title: str | None = None) -> bytes:
    objects: list[bytes] = []
    page_ids = [3 + index * 2 for index in range(len(pages))]
    content_ids = [page_id + 1 for page_id in page_ids]

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = b" ".join(f"{page_id} 0 R".encode() for page_id in page_ids)
    objects.append(
        b"<< /Type /Pages /Kids [" + kids + f"] /Count {len(pages)} >>".encode()
    )
    for page_id, content_id, text in zip(page_ids, content_ids, pages, strict=True):
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {3 + len(pages) * 2} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode()
        )
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET\n".encode()
        objects.append(
            b"<< /Length "
            + str(len(stream)).encode()
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        )
    objects.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    )
    info_id = None
    if title is not None:
        escaped_title = title.replace("\\", "\\\\").replace("(", "\\(").replace(
            ")", "\\)"
        )
        objects.append(f"<< /Title ({escaped_title}) >>".encode())
        info_id = len(objects)

    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{object_number} 0 obj\n".encode())
        result.extend(body)
        result.extend(b"\nendobj\n")
    xref_offset = len(result)
    result.extend(f"xref\n0 {len(offsets)}\n".encode())
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    trailer = f"<< /Size {len(offsets)} /Root 1 0 R"
    if info_id is not None:
        trailer += f" /Info {info_id} 0 R"
    result.extend(f"trailer\n{trailer} >>\n".encode())
    result.extend(f"startxref\n{xref_offset}\n%%EOF\n".encode())
    return bytes(result)


def _encrypted_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("secret")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_ingests_text_pdf_with_digest_title_linkage_and_page_locations(tmp_path):
    content = _pdf_bytes(["First page text.", "Second page text."], title="Study title")
    path = tmp_path / "study.pdf"
    path.write_bytes(content)

    result = ingest_pdf(path)

    assert result.original_filename == "study.pdf"
    assert result.source.title == "Study title"
    assert result.source.content_sha256 == hashlib.sha256(content).hexdigest()
    assert result.source.locator is None
    assert [passage.text for passage in result.passages] == [
        "First page text.",
        "Second page text.",
    ]
    assert [
        (passage.location.page_start, passage.location.page_end)
        for passage in result.passages
    ] == [(1, 1), (2, 2)]
    assert all(
        passage.source_id == result.source.source_id for passage in result.passages
    )
    for passage in result.passages:
        validate_passage_source(result.source, passage)


def test_title_falls_back_to_filename_and_accepts_pdf_without_pdf_extension(tmp_path):
    path = tmp_path / "local-document.data"
    path.write_bytes(_pdf_bytes(["Text without a PDF filename suffix."]))

    result = ingest_pdf(path)

    assert result.original_filename == "local-document.data"
    assert result.source.title == "local-document.data"


def test_passages_are_deterministic_bounded_and_page_scoped(tmp_path):
    text = "word " * 600
    path = tmp_path / "long.pdf"
    path.write_bytes(_pdf_bytes([text, "Independent page."]))

    first = ingest_pdf(path)
    second = ingest_pdf(path)

    first_text_and_locations = [
        (
            passage.text,
            passage.location.page_start,
            passage.location.page_end,
        )
        for passage in first.passages
    ]
    second_text_and_locations = [
        (
            passage.text,
            passage.location.page_start,
            passage.location.page_end,
        )
        for passage in second.passages
    ]
    assert first_text_and_locations == second_text_and_locations
    assert len(first.passages) >= 3
    assert all(len(passage.text) <= 1200 for passage in first.passages)
    page_one_chunks = [
        passage.text for passage in first.passages if passage.location.page_start == 1
    ]
    assert " ".join(page_one_chunks) == text.strip()
    assert [passage.location.page_start for passage in first.passages] == [1, 1, 1, 2]
    assert all(
        passage.location.page_start == passage.location.page_end
        for passage in first.passages
    )


def test_skips_blank_pages_but_preserves_page_numbers(tmp_path):
    path = tmp_path / "blank-page.pdf"
    path.write_bytes(_pdf_bytes(["", "Visible text.", ""]))

    result = ingest_pdf(path)

    assert [passage.text for passage in result.passages] == ["Visible text."]
    assert result.passages[0].location == Location(page_start=2, page_end=2)


@pytest.mark.parametrize("pages", [[], ["", " \t\n"]])
def test_fails_when_pdf_has_no_extractable_nonblank_text(tmp_path, pages):
    path = tmp_path / "empty.pdf"
    path.write_bytes(_pdf_bytes(pages))

    with pytest.raises(PdfIngestionError, match="extractable text"):
        ingest_pdf(path)


def test_missing_path_is_reported_as_ingestion_error(tmp_path):
    with pytest.raises(PdfIngestionError, match="Input path"):
        ingest_pdf(tmp_path / "missing.pdf")


def test_directory_input_is_reported_as_ingestion_error(tmp_path):
    with pytest.raises(PdfIngestionError, match="regular file"):
        ingest_pdf(tmp_path)


@pytest.mark.parametrize(
    "content",
    [
        b"not a pdf",
        b"%PDF-1.4\nbroken",
    ],
)
def test_malformed_pdf_is_reported_as_ingestion_error(tmp_path, content):
    path = tmp_path / "broken.pdf"
    path.write_bytes(content)

    with pytest.raises(PdfIngestionError, match="PDF"):
        ingest_pdf(path)


def test_encrypted_pdf_is_reported_as_unsupported(tmp_path):
    path = tmp_path / "encrypted.pdf"
    path.write_bytes(_encrypted_pdf_bytes())

    with pytest.raises(PdfIngestionError, match="Encrypted"):
        ingest_pdf(path)


def test_page_extraction_failure_is_not_reported_as_success(tmp_path, monkeypatch):
    path = tmp_path / "extraction-failure.pdf"
    path.write_bytes(_pdf_bytes(["Some text."]))
    extraction_error = RuntimeError("page decoder failed")

    class BrokenPage:
        def extract_text(self):
            raise extraction_error

    class Reader:
        is_encrypted = False
        metadata = None
        pages = [BrokenPage()]

    monkeypatch.setattr(
        "scientia.pdf_ingestion.PdfReader", lambda *args, **kwargs: Reader()
    )

    with pytest.raises(PdfIngestionError, match="page 1") as error:
        ingest_pdf(path)

    assert error.value.__cause__ is extraction_error


def test_non_path_input_is_reported_as_ingestion_error():
    with pytest.raises(PdfIngestionError, match="path"):
        ingest_pdf(42)


def test_rejects_pdf_over_byte_limit_before_reading_all_input(tmp_path, monkeypatch):
    content = _pdf_bytes(["small document"])
    path = tmp_path / "small.pdf"
    path.write_bytes(content)
    monkeypatch.setattr(pdf_ingestion, "MAX_PDF_BYTES", len(content), raising=False)

    assert ingest_pdf(path).passages

    path.write_bytes(content + b"x")
    with pytest.raises(PdfIngestionError, match="size limit") as error:
        ingest_pdf(path)

    assert error.value.stage == "validate"


def test_rejects_page_count_over_limit_before_text_extraction(tmp_path, monkeypatch):
    class UnexpectedPage:
        def extract_text(self):
            pytest.fail("page text was extracted before page-count validation")

    class Reader:
        is_encrypted = False
        metadata = None
        pages = [UnexpectedPage(), UnexpectedPage()]

    path = tmp_path / "two-pages.pdf"
    path.write_bytes(_pdf_bytes(["first page", "second page"]))
    monkeypatch.setattr(pdf_ingestion, "MAX_PDF_PAGES", 1, raising=False)
    monkeypatch.setattr(pdf_ingestion, "PdfReader", lambda *args, **kwargs: Reader())

    with pytest.raises(PdfIngestionError, match="page limit") as error:
        ingest_pdf(path)

    assert error.value.stage == "parse"


def test_rejects_cumulative_extracted_text_over_limit(tmp_path, monkeypatch):
    class Page:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class Reader:
        is_encrypted = False
        metadata = None
        pages = [Page("alpha"), Page("bravo")]

    path = tmp_path / "two-pages.pdf"
    path.write_bytes(_pdf_bytes(["first page", "second page"]))
    monkeypatch.setattr(
        pdf_ingestion,
        "MAX_EXTRACTED_TEXT_CHARACTERS",
        9,
        raising=False,
    )
    monkeypatch.setattr(pdf_ingestion, "PdfReader", lambda *args, **kwargs: Reader())

    with pytest.raises(PdfIngestionError, match="extracted text limit") as error:
        ingest_pdf(path)

    assert error.value.stage == "extract"
