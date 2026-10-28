# Governed Real-Research Retrieval Evaluation

## Status

**BLOCKED — no eligible real-research corpus or independently reviewed
relevance labels are established in this repository.** No real-corpus
evaluation or real-world metric has been produced.

The repository includes a root-level `ok.pdf`, but its presence alone does not
establish its source, license, permitted text extraction, or permission to
publish evaluation results. It was not used or inspected as benchmark content.
No provenance-backed corpus manifest or independent real-document judgments
were found in the project materials inspected. The synthetic
`synthetic-lexical-v2` benchmark remains separate and is not evidence of real
research quality.

## Corpus eligibility

Use a small set of public or otherwise appropriately licensed scientific
documents only after a human rights review has verified, for each document:

- a stable document ID, citation, canonical source URL, retrieval date, and
  SHA-256 digest of the exact bytes evaluated;
- the identified license and authoritative license URL;
- explicit permission for acquisition, local storage/text extraction, and
  the intended evaluation reporting or excerpt publication; and
- a durable reference to the source and rights-review evidence.

An accessible URL, public download, search result, or local PDF does not prove
permission. Exclude documents if terms are absent, unclear, incompatible, or
not recorded. Store evidence references, not legal conclusions inferred by
software. The schema in
[`src/scientia/real_evaluation.py`](./src/scientia/real_evaluation.py) validates
required fields and affirmative use declarations; it cannot authenticate
references, interpret a license, or prove the declarations true.

## Reproducible identifiers and query set

Assign versioned corpus IDs and stable opaque document, query, and
document-scoped passage IDs. Preserve the corpus version, protocol version,
document citation/source/license metadata, retrieval date, content hashes,
exact query text, and the rationale for each query. Queries must be defined
before running retrieval and selected to cover the declared research
information needs, including queries expected to have no relevant passage.
Do not derive relevance labels from SCIENTIA's ranking.

## Relevance labels and review

Define relevance at the passage level before labeling (whether the passage
directly addresses the stated information need). Two reviewers independently
label each query/passage pair without seeing the other's label or the
retrieval rank. Record stable pseudonymous reviewer IDs, each binary label,
and references to evidence for reviewer independence and the blinded review
process. Distinct IDs alone do not prove distinct people or independent work;
the referenced evidence requires human verification.

Agreement yields the final binary label. Any disagreement requires a third,
distinct adjudicator, an adjudication rationale, and an evidence reference.
Retain both original labels and the adjudicated result; never silently
overwrite disagreement. Freeze the labels and manifest version before
calculating metrics. If an adjudicator or required evidence is absent, the
manifest is invalid for evaluation.

## Measurement and reporting

Use the existing `retrieve()` ranking and metric implementation. Report
Precision@k, Recall@k, and Reciprocal Rank per query, plus macro means and MRR.
Fix `k` and metric semantics before evaluation. Empty retrieval with judged
relevant passages scores zero for those metrics. Empty relevance judgments
make Recall and Reciprocal Rank undefined and excluded from those means;
report the excluded count. Preserve query-level ranks/scores and the frozen
manifest hash with results. Synthetic and real corpus outputs must never be
combined into a shared metric.

The current package schema deliberately does not calculate or publish metrics
from real documents. Evaluation remains blocked until source rights evidence,
reviewer independence/process evidence, a complete validated manifest, and
independently completed labels have been reviewed and approved for the
intended use.

## Local metadata readiness workflow

The sole CLI input is a UTF-8 JSON metadata manifest; PDFs and evidence
artifacts are not CLI inputs. The manifest has exactly these root keys:
`corpus_id` (nonblank string), `protocol_version` (nonblank string),
`documents`, `queries`, and `judgments` (non-empty arrays).

Each document object must contain:

- `document_id`, `citation`, `license_name`, `rights_evidence_ref`, and
  `rights_review_evidence_ref` (nonblank strings);
- `source_url` and `license_url` (HTTP(S) URLs with a hostname and a
  syntactically valid, in-range port when specified);
- `retrieved_at` (ISO date string) and `content_sha256` (64 lowercase
  hexadecimal characters); and
- `download_allowed`, `text_extraction_allowed`, and
  `evaluation_publication_allowed` (all literal `true`).

Each query object must contain `query_id`, `text`, and `rationale` (nonblank
strings), and `document_ids` (a non-empty array of distinct document IDs from
the manifest).

Each judgment object must contain `query_id`, `document_id`, `passage_id`,
`reviewer_a_id`, `reviewer_b_id`, `independence_evidence_ref`, and
`review_process_evidence_ref` (nonblank strings), plus literal boolean fields
`reviewer_a_relevant` and `reviewer_b_relevant`. The two reviewer IDs must
differ, and the query/document pair must be in scope. If the reviewers
disagree, also provide `adjudicated_relevant` (boolean), a distinct
`adjudicator_id`, a nonblank `adjudication_rationale`, and a nonblank
`adjudication_evidence_ref`. If they agree, those four adjudication fields
must be omitted. The serialized `final_relevant` field is optional; if
provided, it must agree with the reviewer labels and any adjudication.
Passage IDs and evidence references are recorded strings: the schema does not
open documents or referenced evidence to validate them.

See the `RealDocument`, `RealQuery`, `RelevanceJudgment`, and
`RealEvaluationManifest` definitions in
[`src/scientia/real_evaluation.py`](./src/scientia/real_evaluation.py) for the
machine-checked field rules. Create the manifest only from legitimately
obtained corpus metadata and completed independent judgments; do not copy
test fixtures or invent values. Save it as a local `.json` file, then run:

```bash
uv run --locked python -m scientia.real_evaluation --manifest corpus-manifest.json
```

The command validates JSON shape, required fields, dates, digest formatting,
affirmative permitted-use declarations, reference presence, unique IDs,
query/document relationships, distinct reviewer identifiers, and required
third-party adjudication for disagreements. It emits deterministic JSON. A
missing manifest argument, unreadable/missing file, malformed JSON, or
schema-invalid manifest reports `BLOCKED` and exits with code 2. A
schema-valid manifest exits with code 0 to report that field validation
completed, but the JSON still says `status: "BLOCKED"` and
`real_corpus_metrics_produced: false`; code 0 does not mean the corpus is
eligible or approved for evaluation.

This validation only checks supplied field values and internal consistency.
It does not open PDFs, follow evidence references, confirm license terms,
authenticate reviewers, verify independent/blinded review, or establish that
annotations are correct. A human must inspect those sources and record that
review outside this schema before real-corpus evaluation can be considered.

## Limitations and policy status

This protocol does not establish rights, scientific relevance, semantic
understanding, policy approval, or production readiness. It is not an
authorization control. The authorization policy remains
`DRAFT — PENDING OWNER RATIFICATION`; Decisions 11–36 remain
`NOT VERIFIABLE AS NUMBERED`.
