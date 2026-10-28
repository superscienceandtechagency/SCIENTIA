# Consolidated Security and Release Readiness Design

## Purpose and status

This specification covers a safe local prototype hardening pass and a
consolidated evidence-based release assessment. It does not authorize protected
production operations or establish production security.

The authorization policy must remain `DRAFT — PENDING OWNER RATIFICATION`.
Decisions 11–36 must remain `NOT VERIFIABLE AS NUMBERED`. Real-corpus
evaluation must remain blocked unless human-verifiable rights, provenance, and
independent annotation evidence is established.

## Current evidence

- `src/scientia/authorization.py` evaluates caller-supplied immutable facts.
  Its default duration policy denies grant- and assignment-dependent access
  when approved maximums are absent. This module does not authenticate
  identities or load authoritative ownership and policy data.
- `src/scientia/authorization_boundary.py` injects a clock, policy-version
  source, and authorization-facts source and fails closed on provider or
  consistency failures. No trusted production implementations or protected
  operation service are present. Its tests use synthetic providers.
- `src/scientia/cli.py` exposes only the local `prepare` command. It calls the
  real workflow and prints ranked text excerpts. It is not a protected server
  interface.
- `src/scientia/pdf_ingestion.py` currently reads the complete input file,
  parses its pages, and extracts text without a file-size, page-count, or
  cumulative extracted-text ceiling. Passage length is bounded, but total
  work and output are not.
- `src/scientia/real_evaluation.py` validates a metadata-only manifest and
  always keeps readiness `BLOCKED`; it does not calculate real-corpus metrics.
  Python's default JSON parser accepts duplicate object keys by retaining the
  last value, and the CLI does not handle invalid UTF-8 as a manifest
  validation error.
- The project tests exercise domain behavior, synthetic providers, generated
  PDFs, and synthetic retrieval evaluation. They do not prove deployment
  security, authenticated identity, tenant isolation, or external evidence
  authenticity.
- The inspected project configuration has no CI workflow. The project is not
  a Git repository; no commit is part of this work.

## Design

### Bounded local PDF ingestion

Add explicit local input ceilings:

- 64 MiB maximum PDF input.
- 2,000 maximum PDF pages.
- 2,000,000 cumulative extracted text characters.

Read at most one byte over the input ceiling before rejecting an oversized
file; do not call an unbounded whole-file read. Reject excessive page counts
before extracting page text. Track extracted text across pages and fail the
whole ingestion if the total exceeds the ceiling. On any limit failure, raise
the existing `PdfIngestionError` with a stable processing stage and return no
partial result. Existing workflow and CLI error handling must continue to
produce a nonzero result without printing input contents.

These ceilings limit common accidental or oversized local workloads. They do
not sandbox pypdf or guarantee protection from every decompression or parser
resource attack: parsing and extraction may allocate resources before page or
text checks can run. The CLI remains a local development tool for files
selected by its user, not a safe interface for arbitrary hostile uploads.

### Strict, bounded readiness-manifest input

Limit readiness manifests to 10 MiB of encoded UTF-8. The CLI must perform a
bounded read and strict UTF-8 decode. Reject duplicate JSON keys at every
object depth rather than accepting last-value-wins semantics. Treat malformed
UTF-8, duplicate keys, excessive size, invalid JSON, and parser recursion
errors as schema-validation failures. Emit the existing deterministic
`BLOCKED` JSON shape and a nonzero exit code for invalid or unreadable files;
do not leak manifest contents in errors.

Successful field validation continues to report `BLOCKED`. No field,
reference, positive declaration, or schema-valid manifest is to be described
as verified rights, authentic evidence, independent reviewers, or valid
scientific labels.

### Regression coverage

Add tests before production changes for:

- PDF byte-size, page-count, and cumulative-text ceilings, including exact
  boundary acceptance/rejection and no partial result on failure.
- Manifest byte-size limits, duplicate keys at nested and top-level objects,
  invalid UTF-8, and malformed/deep JSON error behavior.
- Deterministic blocked output and nonzero exit status on CLI input failures.
- Retention of successful local CLI behavior and the real-evaluation `BLOCKED`
  state.

### Documentation and release assessment

Update `README.md` only to document the local ceilings, precise local-only
limitations, and a link to one new root-level `RELEASE-READINESS.md`.

The consolidated report must distinguish:

- locally usable prototype features from absent protected production
  operations;
- pure authorization evaluation from authentication and authoritative
  tenant/resource enforcement;
- tested synthetic/local behavior from unverified deployment guarantees;
- schema/field checks from human verification of rights and review evidence;
- completed local checks from infrastructure- or owner-dependent blockers.

The overall report status will be `NOT PRODUCTION READY`. It may state that
the local CLI is available for prototype use, but must not present the
application as production-secure or release-ready for protected multi-tenant
use. It must preserve the exact pending policy and historical record statuses.

## Exclusions

This work will not add authentication, trusted identity, a database,
tenant-scoped persistence, protected routes, grant or assignment lifecycle
workflows, audit storage, external infrastructure, real-corpus documents or
labels, embeddings, or an LLM. It will not inspect or use `ok.pdf` as
corpus material. It will not initialize Git, connect GitHub, or push.

## Verification

After implementation:

1. Run `uv run --locked pytest`.
2. Run `uv run --locked ruff check .`.
3. Run `uv run --locked scientia --help` and the `prepare --help` command.
4. Exercise successful local PDF CLI invocation using a generated temporary
   PDF, without retaining or adding a sample document.
5. Run `uv run --locked python -m scientia.evaluation` twice and compare the
   complete JSON output.
6. Exercise the real-evaluation readiness CLI, verify deterministic blocked
   output, and test invalid-manifest failures without claiming any real-corpus
   readiness.
7. Validate README and report links and exact policy-status language.

Record only observed results. If local checks fail, fix in scope and rerun the
complete required suite before reporting status.
