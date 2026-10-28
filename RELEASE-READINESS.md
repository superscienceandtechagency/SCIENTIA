# SCIENTIA Consolidated Security and Release Readiness

## Status: NOT PRODUCTION READY

The repository supports local development and deterministic synthetic
evaluation. It does not provide the trusted identity, authoritative tenant
ownership, persistence, application-level authorization, revocation, or
durable audit controls needed for protected multi-tenant production use.
Protected operations must remain unavailable. The authorization policy remains
`DRAFT — PENDING OWNER RATIFICATION`; Decisions 11–36 remain
`NOT VERIFIABLE AS NUMBERED`.

This assessment reflects source, tests, package configuration, README, and
readiness/design records in this repository. Unit tests and local tool runs
verify only the stated local behavior; they do not establish deployment
security, policy approval, or external evidence authenticity.

## Gap assessment

| Area | Evidence-based state | Release consequence |
|---|---|---|
| Authorization and identity | [`authorization.py`](./src/scientia/authorization.py) evaluates supplied principal, membership, resource, grant, assignment, and policy facts. Assignment/grant time comparisons and duration checks use UTC instants, including across daylight-saving transitions. [`authorization_boundary.py`](./src/scientia/authorization_boundary.py) remains an injected, non-authenticating seam with no trusted provider implementation. Neither authenticates identity, verifies MFA evidence, nor proves grantor authority or canonical identity. | Do not expose the evaluator or boundary as an application authorization control. No protected route or operation is enabled. |
| Tenant/resource boundary | Scope comparisons exist in the pure evaluator and boundary, but no authoritative identity/membership source, tenant-owned resource repository, storage layer, or protected operation service exists. The boundary tests use synthetic injected providers. | Tenant isolation is not implemented end to end. Caller-supplied local paths do not establish tenant ownership. |
| Revocation and audit | Evaluator records can represent revoked assignments/grants, but there is no lifecycle service, durable current-state source, revoke propagation, operation-time revalidation, or transaction binding. There is no durable audit writer/store or restricted audit-read service. `READ_AUDIT_METADATA` in the evaluator is not an audit system. | Grant/assignment issuance, renewal, protected reads/writes, audit access, deletion, and elevation must remain unavailable. |
| CLI and PDF handling | [`cli.py`](./src/scientia/cli.py) is a local-only `prepare` command that prints ranked excerpts. [`pdf_ingestion.py`](./src/scientia/pdf_ingestion.py) caps each input at 64 MiB, 2,000 pages, and 2,000,000 cumulative extracted characters; [`workflow.py`](./src/scientia/workflow.py) rejects batches above eight PDFs before opening any input. | Suitable only for user-selected local prototype inputs. The limits do not sandbox pypdf or protect against every parser/decompression resource attack; do not accept arbitrary hostile uploads. |
| Real-corpus rights and annotation | [`real_evaluation.py`](./src/scientia/real_evaluation.py) validates metadata structure, not external evidence. Unknown manifest field names are not echoed in validation errors. No eligible corpus with human-verified rights/provenance and independently authenticated labels is established. | Readiness remains `BLOCKED`; no real-corpus retrieval metrics have been produced. Synthetic metrics are not real-research evidence. |
| Tests, packaging, and local execution | The suite checks domain behavior, synthetic authorization providers, generated temporary PDFs, and synthetic retrieval. `pyproject.toml` and `uv.lock` define the Python 3.14 locked environment and `scientia` entry point. Package import, CLI help, local invocation, and source/wheel builds were checked below. No CI workflow was found in the inspected `.github` path. | Local checks are reproducible using the commands below, but no CI/deployment security gate or production integration test exists. |

## Owner-dependent policy blockers

The policy must not be treated as approved until the owner records the ratifier,
date, approved version, and amendments. The [policy draft](./AUTHORIZATION-POLICY-DRAFT.md)
records U-1 as **OWNER-SELECTED — PENDING FORMAL RATIFICATION**: a separate
confidential-content grant may satisfy confidentiality for `READ_RESEARCH`
only if base-role permission and assignment already permit the action; it
adds no action. The evaluator has a corresponding layered check, but that is
only evaluator behavior, not a ratified or service-enforced policy.

The smallest owner decisions still needed before designing the corresponding
workflows are:

- **U-2:** approve the fixed maximum duration for confidential-content grants.
- **U-3:** approve the separate fixed maximum duration for administrator
  elevation.
- **U-4:** approve research-assignment default and maximum durations.
- **U-5:** define who designates security personnel and the scope of their
  authority.
- **U-6:** decide whether issuer and approver need separate operational duties
  beyond distinct identities.
- **U-7:** define canonical identity/account-linking evidence and duplicate
  account handling.
- **U-8:** locate or formally retain the historical Decisions 11–36 record;
  do not reconstruct missing wording or numbering.

The [ratification readiness record](./AUTHORIZATION-RATIFICATION-READINESS.md)
and [integration readiness audit](./AUTHORIZATION-INTEGRATION-READINESS-AUDIT.md)
also identify unresolved identity-provider/session/MFA requirements,
authoritative policy integrity/versioning, the complete role/action matrix,
independent review authority, and audit/retention rules. Numeric values,
provider choices, or policy wording are not inferred here.

## Infrastructure and evidence blockers

Production use requires decisions and independently tested infrastructure that
are not present in this repository:

1. An owner-approved authentication/session/MFA contract and a real adapter
   that validates identity claims and canonical account linkage.
2. Authoritative, tenant-scoped membership, resource, assignment, grant, and
   policy repositories; resource access must use server-derived ownership and
   remain scoped across source files, derived artifacts, caches, and jobs.
3. Operation-level authorization bound to the actual read/write effect,
   current revocation state, transaction/revalidation behavior, and non-
   disclosing failure responses.
4. Grant and assignment lifecycle services with approved durations, authority,
   renewal/revocation semantics, and durable audit events.
5. Restricted, durable, integrity-protected audit storage and owner-approved
   retention, access, deletion, and recovery rules.
6. Cross-tenant and revocation-race integration tests against the actual
   assembled runtime, plus a CI/deployment gate. Synthetic test providers are
   not production evidence.
7. For real-corpus evaluation, human-verified source/license permissions for
   acquisition, extraction, and intended reporting; evidence tied to evaluated
   document bytes; and independently completed labels with reviewer
   independence and disagreement/adjudication evidence.

Until these are supplied and verified, keep confidential reads, protected
public reads, writes, exports, audit access, deletion/purge/restore,
classification changes, review finalization, grant/assignment lifecycle
operations, administrator elevation, and queued protected work unavailable.

## Locally fixed defects and verified protections

- **New defects reproduced and fixed:** `ResearchWorkflowResult` could be
  directly constructed with a reviewed assessment whose evidence referenced a
  passage absent from the prepared corpus, bypassing the provenance validation
  performed by `finalize_research`. The aggregate now enforces source, passage,
  hash, location, and text provenance itself. Separately, synthesis accepted
  duplicate assessment IDs and allowed one `claim_id` to carry different claim
  text; synthesis now rejects both identity inconsistencies while preserving
  separate assessments of the same consistently identified claim.
- **New defect reproduced and fixed:** An exception other than
  `PdfIngestionError` escaping `prepare_research` caused the CLI to emit a
  traceback, including the exception message, and terminate without its
  controlled failure response. The CLI now reports a nonzero, sanitized
  failure with the exception type; regression coverage verifies that message
  and path/content details are not disclosed. Normal `PdfIngestionError`
  diagnostics remain intact.
- **Existing protection, reverified:** Assignment and grant maximum-duration
  checks previously subtracted aware datetimes carrying the same local
  timezone. During a daylight-saving
  fall-back, Python's wall-time subtraction treated 00:30 EDT to 01:30 EST as
  one hour even though two hours elapsed, allowing a two-hour assignment or
  grant under a 90-minute maximum. Comparisons and duration calculations now
  normalize timestamps to UTC. Regression tests reproduce both assignment
  and grant cases.
- **Existing protection, reverified:** `prepare_research` accepted an
  unbounded sequence of individually bounded PDFs and retained all extracted
  passages for retrieval. It now rejects more than eight inputs before opening
  any file; the local CLI returns a sanitized
  nonzero failure. This bounds batch cardinality, not all parser workloads.
- **New defect reproduced and fixed:** A repeated path (including a symlink
  alias) or byte-identical PDF at a second path was ingested as a separate
  source with fresh identifiers, duplicating retrieved evidence. The workflow
  now rejects duplicate resolved paths before ingestion and duplicate
  source-byte SHA-256 digests before retrieval. Content duplication is
  detected after the bounded ingestion.
- **New defect reproduced and fixed:** A `PreparedResearch` record could
  contain an ingested passage with an altered retrieval score or an
  out-of-order hit list. It now validates the supplied hit tuple against the
  deterministic lexical ranking for its question and ingested passages.
  Direct `retrieve()` calls also reject duplicate `(source_id, passage_id)`
  identities instead of emitting repeated hits.
- **Existing protection, reverified:** `finalize_research` rejects unknown
  sources/passages and evidence snapshots with absent or mismatched source
  hashes, page locations, or passage text. Regression coverage explicitly
  checks a missing source hash; this checks supplied provenance, not reviewer
  interpretation or scientific truth.
- **New defect reproduced and fixed:** A `ClaimAssessment` could list the same
  `(source_id, passage_id)` twice with opposing stances and thereby satisfy
  the structural `CONFLICTING` outcome check using only one passage. It now
  rejects duplicate evidence identities within an assessment; conflicting
  stances require distinct passages. This remains a structural check, not
  independent review or proof that either stance is correct.

## Commands and observed results

Executed with the locked project environment:

| Command | Result |
|---|---|
| `uv run --locked pytest` | **359 passed** after the CLI error-handling audit. |
| `uv run --locked ruff check .` | **All checks passed** after the changes. |
| `uv run --locked python -m scientia.verify` | **Passed**: full tests (359 passed), Ruff, `uv lock --check`, package build in a temporary directory, and two byte-identical synthetic evaluation runs. The runner exit status was independently asserted as 0. |
| Focused CLI and workflow tests after the CLI error fix | **9 CLI tests and 43 workflow tests passed**, including Unicode questions, unreadable/missing/malformed files, sanitized unexpected failures, and generated-PDF JSON output. |
| Verification-runner reliability regressions | Missing executable, subprocess timeout, nonzero evaluation exit with stderr details, mismatched outputs, malformed/incorrect-shape evaluation JSON, invalid metric ranges and large numeric values, and build-failure temporary-directory cleanup are covered in `tests/test_verify.py`. Missing executable, timeout, malformed output, and invalid metrics were observed failing before their fixes. |
| `uv run --locked pytest tests/test_authorization.py::test_assignment_duration_uses_elapsed_time_across_dst_fallback tests/test_authorization.py::test_grant_duration_uses_elapsed_time_across_dst_fallback tests/test_workflow.py::test_rejects_unbounded_pdf_batches_before_ingesting_inputs -q` | **3 passed** after implementation; all three failed before the fixes for the intended reasons. |
| `uv run --locked pytest tests/test_authorization.py tests/test_authorization_boundary.py tests/test_workflow.py tests/test_cli.py -q` | **152 passed**, covering the scoped authorization, boundary, workflow, and CLI tests. |
| `uv run --locked pytest tests/test_workflow.py::test_rejects_duplicate_pdf_paths_before_ingesting_inputs tests/test_workflow.py::test_rejects_byte_identical_pdf_inputs_at_different_paths -q` | **2 passed**; each regression was observed failing before its fix. |
| `uv run --locked pytest tests/test_workflow.py::test_prepared_research_rejects_forged_retrieval_score tests/test_workflow.py::test_prepared_research_rejects_reordered_retrieval_hits tests/test_retrieval.py::test_duplicate_passage_identity_is_rejected -q` | **3 passed**; forged score, reordered hits, and duplicate passage identity regressions were observed failing before their fixes. |
| `uv run --locked pytest tests/test_evidence.py tests/test_pdf_ingestion.py tests/test_retrieval.py tests/test_verification.py tests/test_synthesis.py tests/test_workflow.py -q` | **170 passed**; focused evidence, retrieval, PDF provenance, verification, and workflow checks. |
| `uv run --locked pytest tests/test_verification.py tests/test_evidence.py tests/test_pdf_ingestion.py tests/test_retrieval.py tests/test_synthesis.py tests/test_workflow.py` | **171 passed** after the duplicate evidence identity fix. The new regression failed before the fix because the assessment accepted the same passage as both supporting and contradicting. |
| `uv run --locked pytest tests/test_workflow.py::test_finalize_rejects_altered_provenance -q` | **4 passed**, including missing source hash and altered hash, page location, and passage text. |
| `uv run --locked scientia --help` | Passed; help identifies the CLI as local-only and lists `prepare`. |
| `uv run --locked scientia prepare --help` | Passed; required question/PDF arguments and limit are shown. |
| `uv run --locked python -c ...` invoking `uv run --locked scientia prepare` with a generated one-page PDF | Passed; returned one ranked hit attributed to page 1. |
| `uv run --locked pytest tests/test_cli.py::test_cli_runs_local_workflow_and_prints_ranked_excerpts tests/test_cli.py::test_cli_reports_pdf_processing_failure_without_content tests/test_cli.py::test_cli_rejects_missing_file_with_nonzero_exit -q` | **3 passed**; generated-PDF retrieval and sanitized invalid/missing input failures. |
| `uv run --locked python -m scientia.evaluation` (twice; complete output compared) | Identical `synthetic-lexical-v2` results: mean P@3 `0.29166666666666663`, mean R@3 `0.8571428571428571`, MRR `0.7857142857142857`; 7 MRR-included and 1 excluded query. Synthetic results only. |
| `uv run --locked python -c "import scientia; print(scientia.__name__)"` | Passed; printed `scientia`. |
| `uv run --locked pytest tests/test_cli.py::test_cli_runs_local_workflow_and_prints_ranked_excerpts tests/test_cli.py::test_cli_reports_pdf_processing_failure_without_content -q` | **2 passed**. The successful case generates a temporary PDF; the failure case confirms nonzero/sanitized error behavior. |
| `uv run --locked pytest tests/test_real_evaluation.py -q` | **32 passed**, including duplicate-key, byte-limit, invalid UTF-8, recursion-normalization, non-echoing unknown-field errors at each manifest level, and permanently blocked readiness cases. |
| Readiness CLI subprocess smoke with a temporary manifest containing an unknown private field | Exit code 2; emitted `BLOCKED` JSON with no stderr, and neither the field name nor its value appeared in stdout. |
| `uv run --locked python -m scientia.evaluation` (twice, full JSON comparison) | Identical output for `synthetic-lexical-v2`: mean P@3 `0.29166666666666663`, mean R@3 `0.8571428571428571`, MRR `0.7857142857142857`; 7 MRR-included and 1 excluded query. These are synthetic-only results. |
| `uv run --locked python -m scientia.real_evaluation` (twice, full output/status comparison) | Identical `BLOCKED` report, exit code 2 when no manifest is supplied; `real_corpus_metrics_produced` is false. Schema-valid manifests also remain blocked in tests. |
| `uv build --out-dir /tmp/scientia-release-readiness-check` | Successfully built `scientia-0.1.0.tar.gz` and `scientia-0.1.0-py3-none-any.whl`; temporary build artifacts were removed. |
| `uv build --out-dir /tmp/scientia-final-local-prototype` | Successfully built the sdist and wheel for the clean-install check. |
| Clean install: `uv venv <fresh-temp-dir>/venv --python 3.14`, then `uv pip install --python <fresh-temp-dir>/venv/bin/python /tmp/scientia-final-local-prototype/scientia-0.1.0-py3-none-any.whl` | Installed the wheel and its 12 runtime dependencies into a new environment. From outside the repository with `PYTHONPATH` unset, `scientia` imported from that environment's `site-packages`. |
| Installed console script: `scientia --help` and `scientia prepare --help` | Both exited 0; help described the local-only CLI and included the `prepare`, `--question`, and `--pdf` arguments. |
| Installed console script with a generated temporary one-page PDF | Exited 0 and returned one ranked passage containing the generated text; no repository sample or `ok.pdf` was used. |
| Installed console script with repeated invalid and oversized temporary PDFs | Both inputs returned stable exit code 1 on repeat, with empty stdout and no document-content disclosure on stderr. The oversized input was 64 MiB + 1 byte. |
| `uv build --out-dir /tmp/scientia-security-gap-check`, followed by install into a fresh Python 3.14 venv | Successfully built and installed the updated wheel with its runtime dependencies. Installed `scientia --help`, `scientia prepare --help`, and a generated-PDF retrieval smoke all passed from outside the source tree. |
| Updated installed CLI with nine nonexistent PDF paths (run twice) | Stable exit code 1; rejected at the eight-input limit before file access, with no stdout and no path disclosure. |
| README/report link and status check | 11 relative Markdown links checked; 0 missing. The exact pending-policy and historical-status strings were confirmed in the draft and this report. |
| Fresh Python 3.14 wheel installation and CLI smoke, run from a temporary directory with `PYTHONPATH` unset | Build and installation passed; `scientia` and `prepare` help passed; generated-PDF retrieval returned one hit attributed to page 1. Temporary environment and artifacts were removed. |
| Synthetic evaluation run twice after adding the canonical verifier | Identical `synthetic-lexical-v2` output; mean P@3 `0.29166666666666663`, mean R@3 `0.8571428571428571`, MRR `0.7857142857142857`. Synthetic-only results. |

`uv build --locked` was also attempted but this `uv build` command does not
accept `--locked`; rerunning with the supported command above succeeded. No
Git scope check or commit is claimed because this workspace is not a Git
repository. No CI workflow was found under `.github`.

## Finalization integrity audit — latest verification

The finalization audit added provenance enforcement to direct
`ResearchWorkflowResult` construction and synthesis checks for unique
assessment IDs and consistent claim text per claim ID. Regression coverage
rejects those invalid records; the pre-existing inconsistent-partition test
now accepts rejection at either the synthesis or aggregate boundary.

| Command | Result |
|---|---|
| `uv run --locked pytest` | **362 passed**. |
| `uv run --locked ruff check .` | **All checks passed.** |
| `uv run --locked pytest tests/test_verification.py tests/test_synthesis.py tests/test_evidence.py tests/test_workflow.py -q` | **142 passed.** |
| `uv run --locked pytest tests/test_workflow.py::test_finalize_preserves_full_provenance_from_pdf_to_finding -q` | **1 passed**; generated-PDF-to-finding provenance smoke test. |
| `uv run --locked python -m scientia.verify` | **Exit 0**; full test suite (362 passed), Ruff, lockfile consistency, package build, and two identical synthetic evaluation runs all passed. |

## Documentation accuracy audit — latest checks

The README setup command now selects Python 3.14 explicitly, matching the
project's declared `requires-python` range instead of depending on whichever
interpreter happens to be named `python3`. Earlier test counts and command
results above remain historical records rather than being rewritten.

| Command | Result |
|---|---|
| `uv run --locked python -m scientia.verify` | **Exit 0**; 362 tests passed, Ruff passed, lockfile consistency passed, package build passed, and both synthetic evaluation runs matched. |
| `uv run --locked pytest` | **362 passed.** |
| `uv run --locked ruff check .` | **All checks passed.** |
| Relative-link/status consistency check for README, this report, and the policy draft | **21 local relative links resolve**; required `NOT PRODUCTION READY`, `DRAFT — PENDING OWNER RATIFICATION`, and `NOT VERIFIABLE AS NUMBERED` strings are present. |

## Local real-evaluation workflow audit — latest verification

The protocol previously named `RealEvaluationManifest` without listing its
required JSON fields or clarifying the CLI exit-code distinction. The protocol
now documents the root, document, query, and judgment fields, conditional
adjudication fields, metadata-only input boundary, and report semantics. The
README links directly to that field reference. No source or readiness checks
were changed; schema-valid input remains `BLOCKED` and produces no metrics.

| Command | Result |
|---|---|
| `uv run --locked python -m scientia.verify` | **Exit 0**; tests (362 passed), Ruff, lockfile consistency, package build, and both synthetic evaluation runs passed. |
| `uv run --locked pytest` | **Exit 0; 362 passed.** |
| `uv run --locked ruff check .` | **Exit 0; all checks passed.** |
| `uv run --locked python -m scientia.real_evaluation` | **Exit 2**; deterministic JSON reports `BLOCKED`, `manifest not supplied`, and `real_corpus_metrics_produced: false`. |
| `uv run --locked python -m scientia.real_evaluation --manifest /tmp/scientia-manifest-does-not-exist.json` | **Exit 2**; deterministic JSON reports `BLOCKED`, `could not read manifest file`, and `real_corpus_metrics_produced: false`. |

## Security-boundary audit — latest verification

- **Confirmed manifest URL-validation defect and fix:** HTTP(S) URL validation
  previously checked only scheme and non-empty network location, so values
  such as `https://example.org:invalid/article` and port `99999` passed
  document validation. The validator now requires a parsed hostname and
  accesses the parsed port so malformed and out-of-range ports are rejected.
  Focused regression tests for both cases failed before the fix and pass after
  it. This improves metadata syntax checking only; URL references are not
  fetched or authenticated, and manifest readiness remains blocked.

| Command | Result |
|---|---|
| `uv run --locked python -m scientia.verify` | **Exit 0**; tests (364 passed), Ruff, lockfile consistency, package build, and two matching synthetic evaluation runs passed. |
| `uv run --locked pytest` | **Exit 0; 364 passed.** |
| `uv run --locked ruff check .` | **Exit 0; all checks passed.** |
| `uv run --locked pytest tests/test_real_evaluation.py tests/test_pdf_ingestion.py tests/test_cli.py tests/test_authorization.py tests/test_authorization_boundary.py -q` | **Exit 0; 165 passed.** |

## CLI output reliability audit — latest verification

- **Confirmed output failure defect and fix:** Both the local research CLI and
  real-evaluation readiness command previously allowed an `OSError` while
  printing JSON to escape without a controlled return code. Each command now
  explicitly flushes stdout, reports a sanitized stderr error on output
  failure, and returns exit code 1. Focused tests reproduced the uncaught
  errors before the fix and verify the controlled failure afterward. This
  does not guarantee all bytes were written before a downstream output error;
  a partially written JSON document must be treated as failed because the
  command exits nonzero.

| Command | Result |
|---|---|
| `uv run --locked pytest tests/test_cli.py tests/test_real_evaluation.py -q` | **Exit 0; 45 passed.** |
| `uv run --locked python -m scientia.verify` | **Exit 0**; tests (366 passed), Ruff, lockfile consistency, package build, and both synthetic evaluation runs passed. |
| `uv run --locked pytest` | **Exit 0; 366 passed.** |
| `uv run --locked ruff check .` | **Exit 0; all checks passed.** |

## Local evaluation boundary

The synthetic benchmark is a lexical regression measurement over authored
examples, not semantic understanding or real-paper performance. The
real-evaluation readiness command reads only a metadata manifest, rejects
duplicate JSON keys and invalid/oversized UTF-8 input, and reports field/schema
consistency. A schema-valid manifest still does not prove rights, source
authenticity, reviewer independence, or annotation quality and does not
produce real-corpus metrics.

## Latest local verification snapshot — 2026-10-19

Fresh local checks observed on 2026-10-19:

| Command | Result |
|---|---|
| `uv run --locked python -m scientia.verify` | **Exit 0.** Full test suite, Ruff, lockfile consistency, package build, and two synthetic evaluation runs passed; the evaluation outputs matched. |
| `uv run --locked pytest` | **Exit 0; 366 passed.** |
| `uv run --locked ruff check .` | **Exit 0; all checks passed.** |

The repeated evaluation is `synthetic-lexical-v2`; its result is a
deterministic synthetic regression check, not real-corpus or scientific
validation. Real-corpus evaluation remains **BLOCKED** pending eligible corpus
rights/provenance and independently verified relevance-label evidence. The
authorization policy remains **DRAFT — PENDING OWNER RATIFICATION** and
Decisions 11–36 remain **NOT VERIFIABLE AS NUMBERED**. Trusted identity,
tenant-scoped protected operations, durable audit, and production CI/deployment
security controls remain absent. Release status remains **NOT PRODUCTION
READY**. Earlier dated audit results in this report are historical snapshots.

## Final handover and next actions

### Verified local status

As of 2026-10-19, the canonical verifier exits 0, the full suite reports
**366 passed**, and Ruff exits 0. The local prototype supports bounded,
user-selected PDF text extraction, deterministic lexical retrieval, evidence
and claim workflow checks, and synthetic regression evaluation. It does not
provide OCR, semantic or scientific validation, parser sandboxing, trusted
identity, or production authorization.

Reproduce the local checks from the project root:

```bash
uv run --locked python -m scientia.verify
uv run --locked pytest
uv run --locked ruff check .
```

The verifier's synthetic evaluation checks deterministic
`synthetic-lexical-v2` behavior only; it is not real-corpus or scientific
validation. Real-corpus evaluation remains **BLOCKED** as described in the
[evaluation protocol](./REAL-RESEARCH-EVALUATION-PROTOCOL.md).

### Prioritized next actions

1. **Owner:** decide the open policy items U-2–U-8, confirm or amend U-1 and
   selections A–F, then record ratifier, date, approved version, and amendments.
   Keep Decisions 11–36 `NOT VERIFIABLE AS NUMBERED` unless the authoritative
   original record is found. See the [policy draft](./AUTHORIZATION-POLICY-DRAFT.md).
2. **Evaluation evidence owners:** obtain and independently review eligible
   corpus rights/provenance and passage-level relevance-label evidence before
   considering real-corpus evaluation; do not infer this evidence from
   synthetic metrics.
3. **Before any production proposal:** establish a trusted identity and
   tenant-scoped service boundary, operation-time authorization and revocation,
   grant/assignment lifecycle and durable audit controls, then verify the
   assembled runtime with production-representative integration and
   deployment checks. Keep protected operations unavailable until then.

Current outcome: local prototype checks pass; policy ratification and
real-corpus evaluation remain blocked; production controls are not
implemented. **Release status: NOT PRODUCTION READY.**
