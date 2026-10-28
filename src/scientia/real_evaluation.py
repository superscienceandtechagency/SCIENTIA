"""Metadata schema for a future provenance-checked research evaluation."""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

MAX_MANIFEST_BYTES = 10 * 1024 * 1024

HUMAN_VERIFICATION_REQUIRED = (
    "Verify source and license terms permit acquisition and text extraction.",
    "Verify intended evaluation reporting or excerpt publication is permitted.",
    "Verify referenced rights evidence is authentic and applies to the exact "
    "document bytes.",
    "Verify reviewer identities are distinct people and the labeling was "
    "blinded and independent.",
    "Review all query-level labels and any adjudication evidence.",
)


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _require_web_url(value: str, field_name: str) -> None:
    _require_text(value, field_name)
    try:
        parsed = urlparse(value)
        parsed.port
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an HTTP(S) URL") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{field_name} must be an HTTP(S) URL")


@dataclass(frozen=True)
class RealDocument:
    """One document with recorded provenance and required permitted-use facts.

    The rights fields are recorded claims backed by a reference; this record
    does not itself verify the source or interpret its license.
    """

    document_id: str
    citation: str
    source_url: str
    license_name: str
    license_url: str
    retrieved_at: date
    content_sha256: str
    rights_evidence_ref: str
    rights_review_evidence_ref: str
    download_allowed: bool
    text_extraction_allowed: bool
    evaluation_publication_allowed: bool

    def __post_init__(self) -> None:
        for name in (
            "document_id",
            "citation",
            "license_name",
            "rights_evidence_ref",
            "rights_review_evidence_ref",
        ):
            _require_text(getattr(self, name), name)
        _require_web_url(self.source_url, "source_url")
        _require_web_url(self.license_url, "license_url")
        if type(self.retrieved_at) is not date:
            raise TypeError("retrieved_at must be a date")
        if (
            not isinstance(self.content_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.content_sha256) is None
        ):
            raise ValueError("content_sha256 must be a lowercase SHA-256 digest")
        for name in (
            "download_allowed",
            "text_extraction_allowed",
            "evaluation_publication_allowed",
        ):
            value = getattr(self, name)
            if type(value) is not bool:
                raise TypeError(f"{name} must be a boolean")
            if not value:
                raise ValueError(f"{name} must be confirmed before evaluation")


@dataclass(frozen=True)
class RealQuery:
    """A stable query record with its rationale and candidate documents."""

    query_id: str
    text: str
    rationale: str
    document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("query_id", "text", "rationale"):
            _require_text(getattr(self, name), name)
        if not isinstance(self.document_ids, tuple) or not self.document_ids:
            raise ValueError("document_ids must be a non-empty tuple")
        for document_id in self.document_ids:
            _require_text(document_id, "document_id")
        if len(set(self.document_ids)) != len(self.document_ids):
            raise ValueError("document_ids must not contain duplicates")


@dataclass(frozen=True)
class RelevanceJudgment:
    """Two blinded reviewer labels and any required independent adjudication."""

    query_id: str
    document_id: str
    passage_id: str
    reviewer_a_id: str
    reviewer_b_id: str
    reviewer_a_relevant: bool
    reviewer_b_relevant: bool
    independence_evidence_ref: str
    review_process_evidence_ref: str
    adjudicated_relevant: bool | None = None
    adjudicator_id: str | None = None
    adjudication_rationale: str | None = None
    adjudication_evidence_ref: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "query_id",
            "document_id",
            "passage_id",
            "reviewer_a_id",
            "reviewer_b_id",
            "independence_evidence_ref",
            "review_process_evidence_ref",
        ):
            _require_text(getattr(self, name), name)
        if self.reviewer_a_id == self.reviewer_b_id:
            raise ValueError("reviewer IDs must be distinct")
        if type(self.reviewer_a_relevant) is not bool:
            raise TypeError("reviewer_a_relevant must be a boolean")
        if type(self.reviewer_b_relevant) is not bool:
            raise TypeError("reviewer_b_relevant must be a boolean")

        adjudication = (
            self.adjudicated_relevant,
            self.adjudicator_id,
            self.adjudication_rationale,
        )
        if self.reviewer_a_relevant != self.reviewer_b_relevant:
            if self.adjudicated_relevant is None or not self.adjudicator_id:
                raise ValueError("disagreement requires adjudication")
            for name in ("adjudication_rationale", "adjudication_evidence_ref"):
                value = getattr(self, name)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"disagreement requires {name}")
            if self.adjudicator_id in {self.reviewer_a_id, self.reviewer_b_id}:
                raise ValueError("adjudicator must be distinct from both reviewers")
        elif any(
            value is not None
            for value in (*adjudication, self.adjudication_evidence_ref)
        ):
            raise ValueError("adjudication is only valid when reviewers disagree")

        if self.adjudicated_relevant is not None and type(
            self.adjudicated_relevant
        ) is not bool:
            raise TypeError("adjudicated_relevant must be a boolean or None")
        if self.adjudicator_id is not None:
            _require_text(self.adjudicator_id, "adjudicator_id")
        if self.adjudication_rationale is not None:
            _require_text(self.adjudication_rationale, "adjudication_rationale")
        if self.adjudication_evidence_ref is not None:
            _require_text(self.adjudication_evidence_ref, "adjudication_evidence_ref")

    @property
    def final_relevant(self) -> bool:
        if self.reviewer_a_relevant != self.reviewer_b_relevant:
            return self.adjudicated_relevant is True
        return self.reviewer_a_relevant


@dataclass(frozen=True)
class RealEvaluationManifest:
    """Reproducibility manifest; records evidence but does not authenticate it."""

    corpus_id: str
    protocol_version: str
    documents: tuple[RealDocument, ...]
    queries: tuple[RealQuery, ...]
    judgments: tuple[RelevanceJudgment, ...]

    def __post_init__(self) -> None:
        _require_text(self.corpus_id, "corpus_id")
        _require_text(self.protocol_version, "protocol_version")
        for field_name, records, record_type, id_field in (
            ("documents", self.documents, RealDocument, "document_id"),
            ("queries", self.queries, RealQuery, "query_id"),
            ("judgments", self.judgments, RelevanceJudgment, None),
        ):
            if not isinstance(records, tuple):
                raise TypeError(f"{field_name} must be a tuple")
            if not records:
                raise ValueError(f"{field_name} must be non-empty")
            if any(not isinstance(record, record_type) for record in records):
                raise TypeError(f"{field_name} contains an invalid record")
            if id_field is not None:
                identifiers = [getattr(record, id_field) for record in records]
                if len(set(identifiers)) != len(identifiers):
                    raise ValueError(f"{field_name} IDs must not contain duplicates")

        document_ids = {document.document_id for document in self.documents}
        queries_by_id = {query.query_id: query for query in self.queries}
        for query in self.queries:
            if not set(query.document_ids) <= document_ids:
                raise ValueError("query references an unknown document")

        label_keys: set[tuple[str, str, str]] = set()
        for judgment in self.judgments:
            key = (
                judgment.query_id,
                judgment.document_id,
                judgment.passage_id,
            )
            if key in label_keys:
                raise ValueError("judgment IDs must not contain duplicates")
            label_keys.add(key)
            query = queries_by_id.get(judgment.query_id)
            if query is None:
                raise ValueError("judgment references an unknown query")
            if judgment.document_id not in document_ids:
                raise ValueError("judgment references an unknown document")
            if judgment.document_id not in query.document_ids:
                raise ValueError("judgment document is not in the query scope")

    def to_json(self) -> str:
        """Serialize records deterministically without deriving evaluation metrics."""
        payload = {
            "corpus_id": self.corpus_id,
            "protocol_version": self.protocol_version,
            "documents": [
                {
                    **asdict(document),
                    "retrieved_at": document.retrieved_at.isoformat(),
                }
                for document in self.documents
            ],
            "queries": [asdict(query) for query in self.queries],
            "judgments": [
                {
                    **asdict(judgment),
                    "final_relevant": judgment.final_relevant,
                }
                for judgment in self.judgments
            ],
        }
        return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, value: str) -> RealEvaluationManifest:
        """Parse and validate a complete JSON manifest without verifying evidence."""
        if not isinstance(value, str):
            raise TypeError("manifest must be a string")
        if len(value.encode("utf-8")) > MAX_MANIFEST_BYTES:
            raise ValueError("manifest exceeds the configured size limit")
        try:
            payload = json.loads(value, object_pairs_hook=_unique_json_object)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("manifest must be valid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("manifest must be a JSON object")
        _require_exact_fields(
            payload,
            {"corpus_id", "protocol_version", "documents", "queries", "judgments"},
            "manifest",
        )
        if not all(
            isinstance(payload[name], list)
            for name in ("documents", "queries", "judgments")
        ):
            raise ValueError("documents, queries, and judgments must be JSON arrays")
        return cls(
            corpus_id=payload["corpus_id"],
            protocol_version=payload["protocol_version"],
            documents=tuple(_parse_document(item) for item in payload["documents"]),
            queries=tuple(_parse_query(item) for item in payload["queries"]),
            judgments=tuple(_parse_judgment(item) for item in payload["judgments"]),
        )


def _require_exact_fields(
    value: dict[str, object],
    expected: set[str],
    record_name: str,
) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        raise ValueError(f"{record_name} missing fields: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"{record_name} has unknown fields")


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("manifest contains a duplicate JSON key")
        result[key] = value
    return result


def _record_mapping(value: object, record_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{record_name} must be a JSON object")
    return value


def _parse_document(value: object) -> RealDocument:
    item = _record_mapping(value, "document")
    required = {
        "document_id",
        "citation",
        "source_url",
        "license_name",
        "license_url",
        "retrieved_at",
        "content_sha256",
        "rights_evidence_ref",
        "rights_review_evidence_ref",
        "download_allowed",
        "text_extraction_allowed",
        "evaluation_publication_allowed",
    }
    _require_exact_fields(item, required, "document")
    if not isinstance(item["retrieved_at"], str):
        raise ValueError("document.retrieved_at must be an ISO date string")
    try:
        retrieved_at = date.fromisoformat(item["retrieved_at"])
    except ValueError as exc:
        raise ValueError("document.retrieved_at must be an ISO date string") from exc
    return RealDocument(
        document_id=item["document_id"],
        citation=item["citation"],
        source_url=item["source_url"],
        license_name=item["license_name"],
        license_url=item["license_url"],
        retrieved_at=retrieved_at,
        content_sha256=item["content_sha256"],
        rights_evidence_ref=item["rights_evidence_ref"],
        rights_review_evidence_ref=item["rights_review_evidence_ref"],
        download_allowed=item["download_allowed"],
        text_extraction_allowed=item["text_extraction_allowed"],
        evaluation_publication_allowed=item["evaluation_publication_allowed"],
    )


def _parse_query(value: object) -> RealQuery:
    item = _record_mapping(value, "query")
    _require_exact_fields(
        item,
        {"query_id", "text", "rationale", "document_ids"},
        "query",
    )
    document_ids = item["document_ids"]
    if not isinstance(document_ids, list):
        raise ValueError("query.document_ids must be a JSON array")
    return RealQuery(
        query_id=item["query_id"],
        text=item["text"],
        rationale=item["rationale"],
        document_ids=tuple(document_ids),
    )


def _parse_judgment(value: object) -> RelevanceJudgment:
    item = _record_mapping(value, "judgment")
    required = {
        "query_id",
        "document_id",
        "passage_id",
        "reviewer_a_id",
        "reviewer_b_id",
        "reviewer_a_relevant",
        "reviewer_b_relevant",
        "independence_evidence_ref",
        "review_process_evidence_ref",
    }
    optional = {
        "adjudicated_relevant",
        "adjudicator_id",
        "adjudication_rationale",
        "adjudication_evidence_ref",
        "final_relevant",
    }
    _require_exact_fields(item, required | (set(item) & optional), "judgment")
    judgment = RelevanceJudgment(
        query_id=item["query_id"],
        document_id=item["document_id"],
        passage_id=item["passage_id"],
        reviewer_a_id=item["reviewer_a_id"],
        reviewer_b_id=item["reviewer_b_id"],
        reviewer_a_relevant=item["reviewer_a_relevant"],
        reviewer_b_relevant=item["reviewer_b_relevant"],
        independence_evidence_ref=item["independence_evidence_ref"],
        review_process_evidence_ref=item["review_process_evidence_ref"],
        adjudicated_relevant=item.get("adjudicated_relevant"),
        adjudicator_id=item.get("adjudicator_id"),
        adjudication_rationale=item.get("adjudication_rationale"),
        adjudication_evidence_ref=item.get("adjudication_evidence_ref"),
    )
    if "final_relevant" in item:
        if type(item["final_relevant"]) is not bool:
            raise ValueError("judgment.final_relevant must be a boolean")
        if item["final_relevant"] != judgment.final_relevant:
            raise ValueError("judgment.final_relevant does not match its labels")
    return judgment


def readiness_report(manifest_json: str | None = None) -> dict[str, object]:
    """Report metadata validity while preserving the external-evidence block."""
    base: dict[str, object] = {
        "status": "BLOCKED",
        "manifest_schema_valid": False,
        "documents": 0,
        "queries": 0,
        "judgments": 0,
        "field_validation": "not_run",
        "human_verification_required": list(HUMAN_VERIFICATION_REQUIRED),
        "real_corpus_metrics_produced": False,
    }
    if manifest_json is None:
        base["validation_errors"] = ["manifest not supplied"]
        return base
    try:
        manifest = RealEvaluationManifest.from_json(manifest_json)
    except (TypeError, ValueError, RecursionError) as exc:
        base["field_validation"] = "failed"
        base["validation_errors"] = [str(exc)]
        return base

    base.update(
        {
            "manifest_schema_valid": True,
            "documents": len(manifest.documents),
            "queries": len(manifest.queries),
            "judgments": len(manifest.judgments),
            "field_validation": "passed",
        }
    )
    return base


def main(argv: list[str] | None = None) -> int:
    """Print a deterministic local readiness report; never run real metrics."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate local real-evaluation metadata only; readiness remains "
            "blocked pending human evidence verification."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="path to a JSON metadata manifest (does not include document contents)",
    )
    args = parser.parse_args(argv)
    if args.manifest is None:
        report = readiness_report()
        exit_code = 2
    else:
        try:
            with args.manifest.open("rb") as manifest_file:
                manifest_bytes = manifest_file.read(MAX_MANIFEST_BYTES + 1)
        except OSError:
            report = _invalid_manifest_report("could not read manifest file")
            exit_code = 2
        else:
            if len(manifest_bytes) > MAX_MANIFEST_BYTES:
                report = _invalid_manifest_report(
                    "manifest exceeds the configured size limit"
                )
                exit_code = 2
            else:
                try:
                    manifest_json = manifest_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    report = _invalid_manifest_report(
                        "manifest must be valid UTF-8"
                    )
                    exit_code = 2
                else:
                    report = readiness_report(manifest_json)
                    exit_code = 0 if report["manifest_schema_valid"] else 2
    try:
        print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
        sys.stdout.flush()
    except OSError:
        print(
            "scientia: could not write readiness report to standard output",
            file=sys.stderr,
        )
        return 1
    return exit_code


def _invalid_manifest_report(error: str) -> dict[str, object]:
    return {
        "status": "BLOCKED",
        "manifest_schema_valid": False,
        "documents": 0,
        "queries": 0,
        "judgments": 0,
        "field_validation": "failed",
        "validation_errors": [error],
        "human_verification_required": list(HUMAN_VERIFICATION_REQUIRED),
        "real_corpus_metrics_produced": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
