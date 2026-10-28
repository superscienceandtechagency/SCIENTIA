# Readiness Manifest Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make local real-evaluation manifest validation bounded, strict, deterministic, and fail closed while keeping real-corpus readiness blocked.

**Architecture:** Apply a 10 MiB encoded UTF-8 limit to direct and CLI manifest inputs, reject duplicate JSON keys at every nesting level, decode CLI input strictly, and convert malformed/unreadable input into the stable blocked report with a nonzero exit. After this plan and the PDF resource-bounds plan are verified, consolidate the current release assessment into one root report and add README links and command documentation.

**Tech Stack:** Python 3.14 standard library JSON/path handling, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-18-consolidated-release-readiness-design.md`

## Global Constraints

- The authorization policy must remain `DRAFT — PENDING OWNER RATIFICATION`.
- Decisions 11–36 must remain `NOT VERIFIABLE AS NUMBERED`.
- Real-corpus evaluation must remain blocked unless human-verifiable rights, provenance, and independent annotation evidence is established.
- Successful field validation continues to report `BLOCKED`. No field, reference, positive declaration, or schema-valid manifest is to be described as verified rights, authentic evidence, independent reviewers, or valid scientific labels.
- This work will not add authentication, trusted identity, a database, tenant-scoped persistence, protected routes, grant or assignment lifecycle workflows, audit storage, external infrastructure, real-corpus documents or labels, embeddings, or an LLM.
- It will not inspect or use `ok.pdf` as corpus material.
- It will not initialize Git, connect GitHub, or push.
- The overall report status will be `NOT PRODUCTION READY`.
- The workspace is not a Git repository; do not claim a commit or Git scope check.

## Review Focus

- Duplicate JSON keys must be rejected at the top level and inside nested document, query, or judgment records.
- Invalid UTF-8 must produce machine-readable blocked output and a nonzero exit, not a traceback.
- A manifest exactly at 10 MiB must be handled according to the defined inclusive boundary; one byte over must be rejected with bounded reading.
- Any `RecursionError` from the JSON decoder must produce the same fail-closed class of validation report.
- No invalid-input diagnostic may echo manifest contents or imply that a schema-valid manifest has passed human review.

---

### Task 1: Add regression tests for strict manifest parsing

**Files:**
- Modify: `tests/test_real_evaluation.py`
- Reference: `src/scientia/real_evaluation.py`

**Interfaces:**
- Consumes: `RealEvaluationManifest.from_json`, `readiness_report`, and `main`.
- Produces: Tests pinning duplicate-key, size-limit, UTF-8, recursion, deterministic-report, and exit-status behavior.

- [ ] **Step 1: Write a failing duplicate-key test**

Call `readiness_report` on both a repeated top-level field and a repeated nested field. Assert both reports are schema-invalid, remain `BLOCKED`, contain a duplicate-key validation message, and have `real_corpus_metrics_produced is False`.

```python
def test_readiness_report_rejects_duplicate_json_keys():
    for manifest_json in (
        '{"corpus_id":"a","corpus_id":"b"}',
        '{"document":{"source_url":"a","source_url":"b"}}',
    ):
        report = readiness_report(manifest_json)
        assert report["status"] == "BLOCKED"
        assert report["manifest_schema_valid"] is False
        assert report["real_corpus_metrics_produced"] is False
        assert "duplicate" in report["validation_errors"][0]
```

- [ ] **Step 2: Run the duplicate-key test and confirm the expected failure**

Run: `uv run --locked pytest tests/test_real_evaluation.py::test_readiness_report_rejects_duplicate_json_keys -q`

Expected: FAIL because Python's default `json.loads` accepts duplicate keys.

- [ ] **Step 3: Write a failing size-boundary test**

Serialize a valid manifest containing a non-ASCII query character with `ensure_ascii=False`. Monkeypatch the byte limit to the serialized UTF-8 byte length and assert this exact-size manifest remains field-valid and `BLOCKED`; append one ASCII space and assert invalid schema status with a stable size error.

- [ ] **Step 4: Run the size-boundary test and confirm the expected failure**

Run: `uv run --locked pytest tests/test_real_evaluation.py::test_readiness_report_enforces_utf8_byte_size_boundary -q`

Expected: FAIL because neither `from_json` nor the CLI currently caps manifest size.

- [ ] **Step 5: Write failing CLI tests for invalid UTF-8 and decoder errors**

Write `b"\xff"` to a temporary manifest file and call `main(["--manifest", str(path)])`. Assert it returns 2, prints a deterministic JSON `BLOCKED` report to stdout, emits no manifest contents to stderr, and does not raise. Also write a file one byte over a monkeypatched small manifest-size ceiling and assert exit code 2 and blocked JSON without file contents. For decoder recursion normalization, monkeypatch only `json.loads` to raise `RecursionError`; this isolates the error-normalization contract because the current standard-library parser accepts deeply nested arrays without raising.

- [ ] **Step 6: Run the new failure-path tests and confirm the expected failures**

Run:

```bash
uv run --locked pytest tests/test_real_evaluation.py::test_local_readiness_command_reports_invalid_utf8_as_blocked_json -q
uv run --locked pytest tests/test_real_evaluation.py::test_local_readiness_command_rejects_oversized_manifest -q
uv run --locked pytest tests/test_real_evaluation.py::test_readiness_report_normalizes_json_recursion_error -q
```

Expected: FAIL because invalid UTF-8 currently escapes `main` and parser recursion is not normalized by `readiness_report`.

### Task 2: Implement strict, bounded manifest loading

**Files:**
- Modify: `src/scientia/real_evaluation.py`
- Test: `tests/test_real_evaluation.py`

**Interfaces:**
- Consumes: The tests from Task 1 and existing deterministic `BLOCKED` report fields.
- Produces: `MAX_MANIFEST_BYTES = 10 * 1024 * 1024`; a parser that rejects duplicate keys; bounded CLI reads; and a nonzero deterministic report for invalid UTF-8, oversized, malformed, duplicate-key, and recursion-error input.

- [ ] **Step 1: Define a duplicate-key rejecting JSON object hook**

Add a private `object_pairs_hook` that builds a dictionary only when each key is unique. Raise a `ValueError` identifying duplicate-key validation without including the manifest value.

- [ ] **Step 2: Bound direct string parsing**

In `RealEvaluationManifest.from_json`, reject a string whose UTF-8 encoded size exceeds `MAX_MANIFEST_BYTES` before calling `json.loads`; call `json.loads` with the duplicate-key hook.

- [ ] **Step 3: Normalize malformed JSON and decoder recursion errors**

Ensure `readiness_report` converts `TypeError`, `ValueError`, and `RecursionError` into its existing deterministic schema-invalid report. Do not turn failures into a schema-valid report or change the constant `BLOCKED` status.

- [ ] **Step 4: Bound CLI file reads and decode strictly**

Read at most `MAX_MANIFEST_BYTES + 1` bytes from the selected path. Reject excess bytes before decoding; decode with strict UTF-8; convert `OSError` and `UnicodeDecodeError` into the stable blocked JSON shape and nonzero result. Do not print the path contents or exception text that could reveal file data.

- [ ] **Step 5: Run focused manifest tests**

Run: `uv run --locked pytest tests/test_real_evaluation.py -q`

Expected: PASS, including existing valid-manifest, reviewer, adjudication, and deterministic-report tests.

### Task 3: Consolidate release evidence and update user-facing docs

**Files:**
- Create: `RELEASE-READINESS.md`
- Modify: `README.md`
- Verify: `AUTHORIZATION-POLICY-DRAFT.md`, `AUTHORIZATION-IMPLEMENTATION-READINESS.md`, `AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md`, `AUTHORIZATION-RATIFICATION-READINESS.md`, `AUTHORIZATION-FIRST-OPERATION-READINESS.md`, `AUTHORIZATION-ENFORCEMENT-GAP-ASSESSMENT.md`, `REAL-RESEARCH-EVALUATION-PROTOCOL.md`

**Interfaces:**
- Consumes: Actual code behavior and test/lint/smoke outputs after Tasks 1–2 and the PDF resource-bounds plan are complete.
- Produces: One concise report with status `NOT PRODUCTION READY`, exact executed commands/results, blocker evidence and dependencies, and preserved policy/history statuses; README links to that report and documents local-input limits and exact evaluation commands.

- [ ] **Step 1: Gather fresh verification evidence**

Run:

```bash
uv run --locked pytest
uv run --locked ruff check .
uv run --locked scientia --help
uv run --locked scientia prepare --help
uv run --locked python -m scientia.evaluation
uv run --locked python -m scientia.real_evaluation --help
```

Run synthetic evaluation a second time and compare complete JSON output. Invoke the local CLI against a generated temporary PDF with `uv run --locked pytest tests/test_cli.py::test_cli_runs_local_workflow_and_prints_ranked_excerpts -q`. Run the readiness command twice without a manifest and compare complete output and exit status; existing tests must confirm a schema-valid manifest still says `BLOCKED`, while invalid UTF-8 and oversized-manifest tests verify deterministic blocked failures.

- [ ] **Step 2: Write the consolidated readiness assessment**

Record observed results only. Include:

- Pure authorization facts and injected boundary providers are not production authentication or trusted tenant/resource storage.
- Tenant isolation, current revocation data, grant/assignment lifecycle, protected operation mediation, and durable/restricted audit storage are absent.
- Local CLI/PDF operation is available for prototype use and remains outside a protected server boundary.
- Synthetic evaluation metrics are synthetic only; real research remains blocked because rights/provenance and independent labels are not human-verified.
- Tests verify local behavior, not deployment security or real-world scientific retrieval quality.
- The current project has no CI workflow and is not a Git repository; do not claim a commit or Git scope check.
- The policy remains `DRAFT — PENDING OWNER RATIFICATION`; Decisions 11–36 remain `NOT VERIFIABLE AS NUMBERED`.

- [ ] **Step 3: Update README links and local command/security guidance**

Link the single consolidated report. State exact limits, the local-only CLI purpose, synthetic benchmark command, and metadata readiness command. Keep the external rights and reviewer-verification limitation explicit.

- [ ] **Step 4: Validate documentation references and status wording**

Check all new README links resolve to existing files. Confirm the report preserves the exact policy and historical statuses and reports the actual final test/lint/CLI/evaluation outputs.

- [ ] **Step 5: Re-run focused documentation-adjacent regression tests**

Run: `uv run --locked pytest tests/test_cli.py tests/test_pdf_ingestion.py tests/test_real_evaluation.py -q`

Expected: PASS.

## Dependency and execution order

Complete `2026-10-18-local-pdf-resource-bounds.md` before Task 3 here. Tasks 1 and 2 in this plan are independent of the PDF code, but the final release report must be written only after both plans' code and verification steps have completed. Do not claim the global task complete until the full suite and Ruff have been rerun after all edits.
