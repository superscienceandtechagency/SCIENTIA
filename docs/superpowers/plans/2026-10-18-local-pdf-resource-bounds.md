# Local PDF Resource Bounds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bound local PDF file reads, page processing, and extracted text while preserving all-or-nothing ingestion.

**Architecture:** Add byte, page-count, and cumulative extracted-character ceilings to the existing `ingest_pdf` flow. Reject oversize input before parsing, reject excess pages before extraction, and raise the existing `PdfIngestionError` rather than returning partial passages. These local limits do not sandbox pypdf or establish production safety.

**Tech Stack:** Python 3.14, pypdf, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-18-consolidated-release-readiness-design.md`

## Global Constraints

- The authorization policy must remain `DRAFT — PENDING OWNER RATIFICATION`.
- Decisions 11–36 must remain `NOT VERIFIABLE AS NUMBERED`.
- Real-corpus evaluation must remain blocked unless human-verifiable rights, provenance, and independent annotation evidence is established.
- The CLI remains a local development tool for files selected by its user, not a safe interface for arbitrary hostile uploads.
- These ceilings limit common accidental or oversized local workloads. They do not sandbox pypdf or guarantee protection from every decompression or parser resource attack: parsing and extraction may allocate resources before page or text checks can run.
- This work will not add authentication, trusted identity, a database, tenant-scoped persistence, protected routes, grant or assignment lifecycle workflows, audit storage, external infrastructure, real-corpus documents or labels, embeddings, or an LLM.
- It will not inspect or use `ok.pdf` as corpus material.
- It will not initialize Git, connect GitHub, or push.
- The overall report status will be `NOT PRODUCTION READY`.
- The workspace is not a Git repository; do not claim a commit or Git scope check.

## Review Focus

- A file exactly at the byte ceiling must remain accepted; a file one byte over must fail before unbounded reading.
- A PDF with one page beyond the page ceiling must fail before extracting any page text.
- Cumulative extracted text must be measured across pages and fail without returning a partial ingestion result.
- A parser or file-read failure must not be converted into successful empty or partial output.
- The command-line error path must not print the source document contents.

---

### Task 1: Add regression tests for bounded PDF ingestion

**Files:**
- Modify: `tests/test_pdf_ingestion.py`
- Reference: `src/scientia/pdf_ingestion.py`

**Interfaces:**
- Consumes: `ingest_pdf(path: str | Path) -> PdfIngestionResult` and `PdfIngestionError`.
- Produces: Tests that pin the byte/page/text limits and whole-operation failure behavior.

- [ ] **Step 1: Write the failing byte-ceiling test**

Use the existing generated-PDF helper and monkeypatch the production byte ceiling to the exact generated size. Confirm exact-size input succeeds, then add one byte to the file and assert `ingest_pdf` raises `PdfIngestionError` with `stage == "validate"` and no returned result.

```python
def test_rejects_pdf_over_byte_limit_before_reading_all_input(tmp_path, monkeypatch):
    content = _pdf_bytes(["small document"])
    path = tmp_path / "small.pdf"
    path.write_bytes(content)
    monkeypatch.setattr(pdf_ingestion, "MAX_PDF_BYTES", len(content))
    assert ingest_pdf(path).passages

    path.write_bytes(content + b"x")
    with pytest.raises(PdfIngestionError, match="size limit") as error:
        ingest_pdf(path)
    assert error.value.stage == "validate"
```

- [ ] **Step 2: Run the byte-ceiling test and confirm the expected failure**

Run: `uv run --locked pytest tests/test_pdf_ingestion.py::test_rejects_pdf_over_byte_limit_before_reading_all_input -q`

Expected: FAIL because oversized input is currently accepted or read without a size check.

- [ ] **Step 3: Write the failing page-ceiling test**

Generate a valid temporary PDF, set the page ceiling to one, and monkeypatch `PdfReader` with a reader exposing two fake pages. Each fake page's `extract_text()` calls `pytest.fail("page text was extracted before page-count validation")`. Assert ingestion raises `PdfIngestionError` with `stage == "parse"` and the fake page method was never called.

- [ ] **Step 4: Run the page-ceiling test and confirm the expected failure**

Run: `uv run --locked pytest tests/test_pdf_ingestion.py::test_rejects_page_count_over_limit_before_text_extraction -q`

Expected: FAIL because page count is currently not bounded.

- [ ] **Step 5: Write the failing cumulative-text test**

Generate a valid temporary PDF, monkeypatch `PdfReader` with two pages returning `"alpha"` and `"bravo"`, and set `MAX_EXTRACTED_TEXT_CHARACTERS` to 9. Assert a `PdfIngestionError` with `stage == "extract"` instead of a partial `PdfIngestionResult`.

- [ ] **Step 6: Run the cumulative-text test and confirm the expected failure**

Run: `uv run --locked pytest tests/test_pdf_ingestion.py::test_rejects_cumulative_extracted_text_over_limit -q`

Expected: FAIL because only passage length is currently bounded, not total extracted text.

### Task 2: Implement PDF resource ceilings

**Files:**
- Modify: `src/scientia/pdf_ingestion.py`
- Test: `tests/test_pdf_ingestion.py`

**Interfaces:**
- Consumes: Regression tests and the current `PdfIngestionError` contract.
- Produces: `MAX_PDF_BYTES = 64 * 1024 * 1024`, `MAX_PDF_PAGES = 2_000`, and `MAX_EXTRACTED_TEXT_CHARACTERS = 2_000_000`; `ingest_pdf` rejects violations before returning any result.

- [ ] **Step 1: Read at most one byte over the PDF byte ceiling**

Replace unbounded `Path.read_bytes()` with a binary stream read capped at `MAX_PDF_BYTES + 1`. If the extra byte is present, raise `PdfIngestionError` without passing bytes to `PdfReader`. Preserve the existing sanitized read-error behavior and hash the exact accepted byte sequence.

- [ ] **Step 2: Reject excessive page counts before extraction**

After obtaining `page_count`, raise `PdfIngestionError` with a stable parse/validation stage if `page_count > MAX_PDF_PAGES`. Do not extract page text in this case.

- [ ] **Step 3: Enforce the cumulative extracted-character ceiling**

Maintain a count across page text and reject when the next page would exceed `MAX_EXTRACTED_TEXT_CHARACTERS`. Keep the current page-scoped passage splitting and all-or-nothing exception behavior. Do not return partial passages.

- [ ] **Step 4: Run the focused PDF suite**

Run: `uv run --locked pytest tests/test_pdf_ingestion.py -q`

Expected: PASS, including existing page-location, splitting, malformed-PDF, and extraction-failure tests.

### Task 3: Document local PDF limits and verify the CLI error path

**Files:**
- Modify: `README.md`
- Test: `tests/test_cli.py`
- Verify: `src/scientia/cli.py`

**Interfaces:**
- Consumes: The configured limits from `scientia.pdf_ingestion` and the existing generic `PdfIngestionError` CLI handling.
- Produces: Accurate README limits and verification that ingestion-limit failures produce a nonzero exit without document contents in stderr.

- [ ] **Step 1: Verify existing CLI error-path coverage**

Confirm `tests/test_cli.py::test_cli_reports_pdf_processing_failure_without_content` covers nonzero exit, empty stdout, and exclusion of input contents. The new size-limit branch raises the same `PdfIngestionError` type; the dedicated new boundary test is `tests/test_pdf_ingestion.py::test_rejects_pdf_over_byte_limit_before_reading_all_input`.

- [ ] **Step 2: Run the existing CLI error-path and new byte-limit regressions**

Run:

```bash
uv run --locked pytest tests/test_cli.py::test_cli_reports_pdf_processing_failure_without_content -q
uv run --locked pytest tests/test_pdf_ingestion.py::test_rejects_pdf_over_byte_limit_before_reading_all_input -q
```

Expected: PASS; the generic sanitized error path handles `PdfIngestionError`, and the byte-ceiling test proves its new cause.

- [ ] **Step 3: Update README with exact limits and remaining risk**

In the local PDF ingestion and local research CLI sections, state the 64 MiB, 2,000-page, and 2,000,000-character limits; explain that limits do not sandbox pypdf or permit arbitrary hostile PDF uploads.

- [ ] **Step 4: Run PDF and CLI tests**

Run: `uv run --locked pytest tests/test_pdf_ingestion.py tests/test_cli.py -q`

Expected: PASS.

## Verification

The final integrated plan runs the complete suite, Ruff, installed CLI help, a generated temporary-PDF invocation, synthetic evaluation twice, real-readiness CLI checks, and documentation-link checks.
