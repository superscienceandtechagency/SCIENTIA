# SCIENTIA

SCIENTIA is a research-oriented system for scientific literature analysis and
evidence-grounded retrieval. The repository includes a minimal Python
foundation, an Evidence Domain, and local text-based PDF ingestion.

## Evidence Domain

The standard-library domain records `Source`, `Passage`, and `Location`
preserve source and passage identities, exact passage text, and page or section
locations when available. Unknown location is represented as `None`; records
do not infer missing metadata. Source linkage provides provenance only and does
not verify that a scientific claim is supported by a passage.

## Claim-to-Evidence Verification

`Claim`, `EvidenceObservation`, and `ClaimAssessment` are immutable records for
human-entered judgments; they do not automatically classify evidence.
`EvidenceObservation.from_source_passage(source, passage, stance)` verifies the
source/passage link and snapshots the passage and source IDs, source SHA-256
when available, location when available, and exact passage text.

Evidence stances describe one passage: `SUPPORTS` means the reviewer judges it
to support the claim; `CONTRADICTS` means it conflicts with the claim;
`IRRELEVANT` means it does not bear on the claim; and `UNCLEAR` means its
relationship cannot be determined. Assessment outcomes summarize the reviewed
set: `SUPPORTED` means at least one passage is judged supportive;
`CONTRADICTED` means at least one is judged contradictory;
`INSUFFICIENT_EVIDENCE` means the available passages establish neither support
nor contradiction; and `CONFLICTING` means the set contains both supporting and
contradicting observations. Insufficient evidence is not a contradiction.
An assessment containing both supporting and contradicting observations must
use `CONFLICTING`; validation rejects other outcomes rather than rewriting them.
Draft and clarification-needed assessments can remain unresolved with no
outcome.

Validation checks record consistency only. It does not establish semantic
entailment, source quality, or scientific truth, and retrieval scores or ranks
do not determine stances. PDF text extraction may omit or misrepresent content;
a source hash identifies the original bytes, not their accuracy or authority.
Ingestion-generated UUIDs can change on reingestion, so they are not stable
cross-import identifiers.

## Research Synthesis

`synthesize(question, assessments)` organizes caller-supplied assessments into
immutable `SynthesisFinding` and unresolved-assessment tuples. A finding wraps
the original `ClaimAssessment` and is included only when it is
`HUMAN_REVIEWED` and has an outcome. Drafts, clarification-needed assessments,
and assessments without an outcome remain unresolved. Input order is preserved
within both groups, and separate assessments for the same claim remain
separate. Within one synthesis, assessment IDs must be unique, and repeated
claim IDs must retain the same claim text.

The operation preserves each assessment and its evidence snapshots unchanged,
including source and passage IDs, source hashes and locations when available,
exact passage text, and conflicting support/contradiction observations.
`INSUFFICIENT_EVIDENCE` remains distinct from `CONTRADICTED`. Since ingestion
can assign new UUIDs on reingestion, those IDs are not stable cross-import
identifiers.

This layer requires prior human review for findings. It does not infer whether
an assessment is relevant to the research question, use retrieval scores or
ranks as evidence, establish scientific truth, or generate conclusions.

## End-to-End Research Workflow

`prepare_research(question, pdf_paths, limit=10)` ingests local PDFs in the
given order, preserves each `PdfIngestionResult`, flattens its passages in
that order, then retrieves against the exact question text. It returns a
`PreparedResearch` with ingestion results and ranked hits. Invalid PDF input
propagates `PdfIngestionError`; preparation fails as a whole rather than
returning partial results. An empty hit tuple is valid and does not imply
absence or contradiction.

After a person supplies `ClaimAssessment` records,
`finalize_research(prepared, assessments)` verifies every evidence observation
against the ingested source and passage: IDs, source hash, location, and exact
text must match. A valid passage need not have been a retrieval hit. The
workflow does not create or approve assessments, and uses the existing
synthesis operation to keep reviewed findings separate from unresolved
assessments. Insufficient evidence and conflicting evidence remain distinct.
Within one assessment, each `(source_id, passage_id)` may appear only once;
conflicting support and contradiction therefore require distinct passages.
The `ResearchWorkflowResult` aggregate enforces the same provenance checks
even when constructed directly, so a workflow result cannot be assembled around
an assessment referencing a passage outside its prepared corpus.

Provenance is carried from the source-byte digest and page-scoped passage into
the observation, assessment, and finding without alteration. Retrieval scores
only rank passages; they do not determine an evidence stance or outcome. This
local orchestration is deterministic for fixed records and inputs, but
ingestion-generated UUIDs can differ across separate runs. It does not establish
scientific truth, infer question relevance, or generate conclusions.

## Local PDF ingestion

`ingest_pdf(path)` reads a local PDF, records its SHA-256 digest, and returns a
source with page-linked passages. Passages are split deterministically at
whitespace boundaries up to 1,200 characters and never span pages. Invalid,
encrypted, unextractable, or failed PDFs raise `PdfIngestionError`.

```python
from scientia.pdf_ingestion import ingest_pdf

result = ingest_pdf("paper.pdf")
source = result.source
passages = result.passages
```

This milestone uses pypdf text extraction only. It does not perform OCR,
guarantee layout fidelity, retain the original PDF, or verify that a claim is
supported by an extracted passage. Local ingestion limits input PDFs to 64 MiB,
2,000 pages, and 2,000,000 cumulative extracted text characters. These limits
reduce oversized local workloads but do not sandbox pypdf or guarantee
protection from every parser or decompression resource attack.

## Local research CLI

Install the project in its locked environment, then run the local development
command with one or more explicitly selected PDFs:

```bash
uv run --locked scientia prepare \
  --question "What evidence concerns intervention X?" \
  --pdf paper-one.pdf \
  --pdf paper-two.pdf
```

The command runs `prepare_research` and writes ranked retrieval excerpts as
JSON to standard output. It reads caller-supplied local paths under the
current process's filesystem permissions; it does not establish identity,
tenant ownership, or authorization and is not a production-secure or
multi-tenant interface. Do not use it as a substitute for protected server-side
operations. Invalid PDF inputs return a nonzero exit with a sanitized
diagnostic. Unexpected processing exceptions are reported as failures by
exception type without printing exception messages, document content, or paths.
If writing the JSON result to standard output fails, the command reports a
sanitized error on standard error and returns nonzero.

The same local ingestion ceilings apply: 64 MiB per PDF, 2,000 pages, and
2,000,000 extracted text characters. A workflow accepts at most eight PDF
inputs, rejects duplicate resolved paths and byte-identical content, and does
so to avoid repeated excerpts being treated as separate evidence. Do not use
the CLI to process arbitrary hostile uploads.

## Baseline retrieval

`retrieve(query, passages, limit=10)` ranks existing passages by the number
of distinct case-folded query tokens they share. Ties are ordered by source
UUID and passage UUID; returned hits preserve the original passage and its
provenance. Duplicate `(source_id, passage_id)` inputs are rejected rather
than ranked as repeated evidence. `PreparedResearch` validates that its hits
and scores match the deterministic ranking for its question and ingested
passages. This local lexical baseline has no model or service dependency. It
does not understand synonyms or establish that a passage supports a claim.

## Pure authorization kernel

`scientia.authorization.authorize` evaluates one action against immutable
principal, membership, resource, assignment, and grant facts. It is a
deterministic policy function, not an authentication or application service:
callers must supply trustworthy identity and ownership facts. It does not
verify OIDC claims, MFA, account linking, grantor authority, or whether
accounts represent distinct people. Grant facts must identify distinct
grantee, issuer, and approver identities, but this evaluator cannot verify that
those identities are authentic or that the issuer/approver were authorized.

The kernel defaults to denial for unknown or unsupported actions, mismatched
tenant/workspace scope, and missing context. Assignment- and grant-based
decisions also deny unless a maximum duration is explicitly supplied in the
policy; no approved duration defaults are configured. The module does not
create, approve, renew, or revoke grants or assignments, and does not provide
API routes, persistence, audit storage, queues, or production tenant
isolation. It is not a complete representation of the approved policy record:
Decisions 11–36 remain unverified as numbered, and undefined permissions
remain denied. Non-disclosing service responses and audit-read recording are
also not implemented here.

At the evaluator level, a confidential `READ_RESEARCH` requires the existing
role and active-assignment path as well as a valid scoped read grant; neither
the grant nor assignment alone supplies the other's permission. The kernel
currently defines no role-only `WRITE_RESEARCH` or `EXPORT_RESEARCH` allow
path, so a matching grant alone is denied for those actions. These restrictions
do not ratify the pending policy or provide authentication, grant issuance,
assignment lifecycle, or service-boundary enforcement.

## Retrieval evaluation benchmark

Run the fixed synthetic benchmark and per-query failure report with:

```bash
uv run --locked python -m scientia.evaluation
```

Benchmark `synthetic-lexical-v2` uses manually authored relevance labels,
independent of retriever output. At `k=3`, Precision@k divides relevant
retrieved passages by 3 (including unfilled ranks); Recall@k divides by all
judged relevant passages; reciprocal rank is the inverse first relevant rank.
Queries with no judged relevant passages have undefined Recall@k and reciprocal
rank and are excluded from mean Recall@k and MRR; Precision@k includes all
queries. Queries with relevant judgments but no retrieved results score zero
for all three metrics. The JSON report represents undefined metrics as `null`
and counts MRR-included and excluded queries. Each query includes its fixed
label rationale, ranked passage IDs and lexical scores, judged relevant
passages missed within the top three, irrelevant retrieved IDs, and pairwise
ranking errors where an irrelevant result precedes a retrieved relevant one.
For queries without relevance judgments, failure diagnostics are `null`
instead of treating unjudged results as known false positives.

The benchmark retains four baseline cases and adds exact
phrase, partial lexical match, an irrelevant high-overlap decoy, and a
terminology-mismatch case. Labels are assigned from the explicitly authored
synthetic passage scenarios and are not inferred from retriever output.

For v2, mean Precision@3 is `7/24` (about 0.2917), mean Recall@3 is `6/7`
(about 0.8571), and MRR is `11/14` (about 0.7857) across seven judged queries.
The unjudged astronomy query is excluded from mean Recall@3 and MRR. The
cellular-energy decoy ranks ahead of its relevant result (RR 0.5); the
terminology-mismatch query retrieves no passage despite one relevant label
(Recall@3 and RR 0); the partial-saline query retrieves an irrelevant lexical
match alongside its relevant result.

This is a small synthetic regression benchmark for deterministic behavior, not
evidence of semantic understanding, real-world scientific retrieval quality,
or claim support. The labels are judgments about constructed examples only;
they do not establish how real research papers should be judged or whether
retrieval is useful in production. It does not establish production readiness.

## Real-research evaluation status

Real-corpus evaluation is blocked until source/license permissions and
independently reviewed passage-level labels are evidenced and recorded. A
local PDF is not presumed licensed based on accessibility. See the
[real-research evaluation protocol](./REAL-RESEARCH-EVALUATION-PROTOCOL.md)
and the metadata schema/workflow in
[`scientia.real_evaluation`](./src/scientia/real_evaluation.py). To validate a
locally prepared metadata-only JSON manifest and print its readiness report:

```bash
uv run --locked python -m scientia.real_evaluation --manifest corpus-manifest.json
```

The command never reads document contents, downloads files, or calculates real
retrieval metrics. It validates required fields, IDs, references, reviewer
distinction, and disagreement/adjudication consistency. Even a schema-valid
manifest reports `BLOCKED`: the fields and evidence references are claims
requiring human verification of license terms, evidence authenticity, actual
reviewer independence/blinding, and label quality. Do not treat schema
validation as rights clearance or approval. Manifests are limited to 10 MiB,
must be valid UTF-8, and duplicate JSON keys are rejected. No real-corpus
metrics have been run. If writing the JSON readiness report fails, the command
reports a sanitized error on standard error and returns exit code 1.

The [real-research evaluation protocol](./REAL-RESEARCH-EVALUATION-PROTOCOL.md#local-metadata-readiness-workflow)
lists the exact manifest fields and explains exit codes. The command takes
one metadata JSON file, not PDFs or evidence artifacts. Exit code 0 means only
that manifest fields passed validation; the report remains `BLOCKED` until the
corpus rights and independent-label evidence are verified for the intended
use. Missing or invalid input reports `BLOCKED` and exits 2.

## Development setup

Use Python 3.14 and [uv](https://docs.astral.sh/uv/). From the project root:

```bash
uv venv --python 3.14 .venv
uv lock
uv sync --locked
```

The virtual environment is project-local at `.venv/`. `uv.lock` records the
resolved dependency versions. The installed package declares `pypdf` as its
only third-party runtime dependency; `httpx`, `pytest`, and `ruff` are confined
to the development dependency group. Do not activate or modify a global Python
environment to work on this project.

## Local verification

Run the canonical local verification command from the project root:

```bash
uv run --locked python -m scientia.verify
```

It runs the full test suite, Ruff, lockfile consistency, a package build in a
temporary directory, and the synthetic evaluation twice to check deterministic
output. Each check reports its status; any failed command or evaluation
mismatch makes the runner exit nonzero. Each subprocess has a ten-minute
timeout; missing commands and timeouts are reported as failures while later
checks continue. Evaluation output must match the expected synthetic benchmark
report shape, including finite metrics in the range `[0, 1]`. It does not
perform a clean-environment installation or a production-security assessment.

## Release readiness

The current consolidated assessment is
[NOT PRODUCTION READY](./RELEASE-READINESS.md). Local commands and synthetic
evaluation are usable for prototype development only; they do not provide
trusted authentication, tenant isolation, protected server operations, or
verified real-corpus evidence.
