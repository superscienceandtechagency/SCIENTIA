import json
import sys
from dataclasses import replace
from datetime import date

import pytest

import scientia.real_evaluation as real_evaluation
from scientia.real_evaluation import (
    RealDocument,
    RealEvaluationManifest,
    RealQuery,
    RelevanceJudgment,
    main,
    readiness_report,
)


def _document() -> RealDocument:
    return RealDocument(
        document_id="paper-001",
        citation="Example et al. (2024), Synthetic citation.",
        source_url="https://example.org/article",
        license_name="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        retrieved_at=date(2026, 10, 18),
        content_sha256="a" * 64,
        rights_evidence_ref="rights-review-001",
        download_allowed=True,
        text_extraction_allowed=True,
        evaluation_publication_allowed=True,
        rights_review_evidence_ref="rights-review-artifact-001",
    )


def _query() -> RealQuery:
    return RealQuery(
        query_id="query-001",
        text="What is the primary outcome?",
        rationale="Derived from the stated research question.",
        document_ids=("paper-001",),
    )


def _label() -> RelevanceJudgment:
    return RelevanceJudgment(
        query_id="query-001",
        document_id="paper-001",
        passage_id="paper-001-p1",
        reviewer_a_id="reviewer-a",
        reviewer_b_id="reviewer-b",
        reviewer_a_relevant=True,
        reviewer_b_relevant=True,
        independence_evidence_ref="reviewer-independence-001",
        review_process_evidence_ref="blind-review-process-001",
    )


def _manifest() -> RealEvaluationManifest:
    return RealEvaluationManifest(
        corpus_id="governed-research-v1",
        protocol_version="1",
        documents=(_document(),),
        queries=(_query(),),
        judgments=(_label(),),
    )


def test_manifest_serializes_with_stable_provenance_and_double_labels():
    manifest = _manifest()

    first = manifest.to_json()
    second = manifest.to_json()

    assert first == second
    payload = json.loads(first)
    assert payload["documents"][0]["content_sha256"] == "a" * 64
    assert payload["queries"][0]["query_id"] == "query-001"
    assert payload["judgments"][0]["reviewer_a_relevant"] is True
    assert payload["judgments"][0]["final_relevant"] is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("download_allowed", False),
        ("text_extraction_allowed", False),
        ("evaluation_publication_allowed", False),
        ("rights_evidence_ref", ""),
        ("rights_review_evidence_ref", ""),
        ("content_sha256", "not-a-hash"),
    ],
)
def test_document_rejects_missing_or_insufficient_rights_evidence(field, value):
    with pytest.raises((TypeError, ValueError)):
        replace(_document(), **{field: value})


@pytest.mark.parametrize(
    "url",
    [
        "https://example.org:invalid/article",
        "https://example.org:99999/article",
    ],
)
def test_document_rejects_http_urls_with_invalid_ports(url):
    with pytest.raises(ValueError, match="HTTP\\(S\\) URL"):
        replace(_document(), source_url=url)


def test_judgment_rejects_same_reviewer_identity():
    with pytest.raises(ValueError, match="distinct"):
        replace(_label(), reviewer_b_id="reviewer-a")


def test_disagreement_requires_a_distinct_adjudicator_and_rationale():
    with pytest.raises(ValueError, match="adjudication"):
        replace(_label(), reviewer_b_relevant=False)

    with pytest.raises(ValueError, match="adjudicator"):
        replace(
            _label(),
            reviewer_b_relevant=False,
            adjudicated_relevant=True,
            adjudicator_id="reviewer-a",
            adjudication_rationale="Reviewed source passage.",
            adjudication_evidence_ref="adjudication-record-001",
        )

    resolved = replace(
        _label(),
        reviewer_b_relevant=False,
        adjudicated_relevant=True,
        adjudicator_id="adjudicator-c",
        adjudication_rationale="Reviewed source passage.",
        adjudication_evidence_ref="adjudication-record-001",
    )
    assert resolved.final_relevant is True


def test_manifest_rejects_missing_independence_evidence_or_empty_dataset():
    with pytest.raises(ValueError, match="review_process_evidence_ref"):
        replace(_label(), review_process_evidence_ref="")

    with pytest.raises(ValueError, match="adjudication"):
        replace(
            _label(),
            reviewer_b_relevant=False,
            adjudicated_relevant=True,
            adjudicator_id="adjudicator-c",
            adjudication_rationale="Reviewed source passage.",
        )

    with pytest.raises(ValueError, match="non-empty"):
        replace(_manifest(), judgments=())


def test_manifest_rejects_duplicate_and_dangling_ids():
    with pytest.raises(ValueError, match="duplicate"):
        replace(_manifest(), documents=(_document(), _document()))

    dangling = replace(_label(), query_id="unknown-query")
    with pytest.raises(ValueError, match="query"):
        replace(_manifest(), judgments=(dangling,))


def test_manifest_rejects_query_document_mismatch():
    query = replace(_query(), document_ids=("missing-paper",))

    with pytest.raises(ValueError, match="document"):
        replace(_manifest(), queries=(query,))


def test_readiness_report_is_blocked_even_when_manifest_schema_is_valid():
    report = readiness_report(_manifest().to_json())

    assert report == {
        "status": "BLOCKED",
        "manifest_schema_valid": True,
        "documents": 1,
        "queries": 1,
        "judgments": 1,
        "field_validation": "passed",
        "human_verification_required": [
            "Verify source and license terms permit acquisition and text extraction.",
            "Verify intended evaluation reporting or excerpt publication is permitted.",
            "Verify referenced rights evidence is authentic and applies to the "
            "exact document bytes.",
            "Verify reviewer identities are distinct people and the labeling "
            "was blinded and independent.",
            "Review all query-level labels and any adjudication evidence.",
        ],
        "real_corpus_metrics_produced": False,
    }


@pytest.mark.parametrize(
    "manifest_json",
    [
        "{",
        json.dumps({"corpus_id": "missing-records"}),
        json.dumps({"documents": [], "queries": [], "judgments": []}),
    ],
)
def test_readiness_report_handles_malformed_or_incomplete_manifests(manifest_json):
    report = readiness_report(manifest_json)

    assert report["status"] == "BLOCKED"
    assert report["manifest_schema_valid"] is False
    assert report["real_corpus_metrics_produced"] is False
    assert report["validation_errors"]
    assert readiness_report(manifest_json) == report


def test_manifest_json_parser_rejects_unknown_fields_and_bad_dates():
    payload = json.loads(_manifest().to_json())
    payload["documents"][0]["retrieved_at"] = "not-a-date"

    report = readiness_report(json.dumps(payload))

    assert report["status"] == "BLOCKED"
    assert report["manifest_schema_valid"] is False
    assert any("retrieved_at" in error for error in report["validation_errors"])


@pytest.mark.parametrize(
    "record",
    ["manifest", "documents", "queries", "judgments"],
)
def test_readiness_report_does_not_echo_unknown_manifest_fields(record):
    payload = json.loads(_manifest().to_json())
    extra_field = "private_payload_marker"
    if record == "manifest":
        payload[extra_field] = "private value"
    else:
        payload[record][0][extra_field] = "private value"

    report = readiness_report(json.dumps(payload))
    serialized_report = json.dumps(report)

    assert report["status"] == "BLOCKED"
    assert report["manifest_schema_valid"] is False
    assert extra_field not in serialized_report
    assert "private value" not in serialized_report


def test_manifest_parser_rejects_forged_derived_final_label():
    payload = json.loads(_manifest().to_json())
    payload["judgments"][0]["final_relevant"] = False

    report = readiness_report(json.dumps(payload))

    assert report["status"] == "BLOCKED"
    assert report["manifest_schema_valid"] is False
    assert "final_relevant" in report["validation_errors"][0]


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


def test_readiness_report_enforces_utf8_byte_size_boundary(monkeypatch):
    payload = json.loads(_manifest().to_json())
    payload["queries"][0]["text"] = "café"
    manifest_json = json.dumps(payload, ensure_ascii=False)
    manifest_size = len(manifest_json.encode("utf-8"))
    monkeypatch.setattr(
        real_evaluation,
        "MAX_MANIFEST_BYTES",
        manifest_size,
        raising=False,
    )

    exact_limit_report = readiness_report(manifest_json)
    over_limit_report = readiness_report(manifest_json + " ")

    assert exact_limit_report["status"] == "BLOCKED"
    assert exact_limit_report["manifest_schema_valid"] is True
    assert over_limit_report["status"] == "BLOCKED"
    assert over_limit_report["manifest_schema_valid"] is False
    assert "size limit" in over_limit_report["validation_errors"][0]


def test_local_readiness_command_reports_invalid_utf8_as_blocked_json(
    tmp_path, capsys
):
    manifest_path = tmp_path / "invalid-utf8.json"
    manifest_path.write_bytes(b"\xff")

    exit_code = main(["--manifest", str(manifest_path)])
    first_output = capsys.readouterr()
    repeated_exit_code = main(["--manifest", str(manifest_path)])
    repeated_output = capsys.readouterr()

    assert exit_code == 2
    assert repeated_exit_code == exit_code
    assert repeated_output == first_output
    assert first_output.err == ""
    assert json.loads(first_output.out)["status"] == "BLOCKED"


def test_local_readiness_command_rejects_oversized_manifest(
    tmp_path, monkeypatch, capsys
):
    manifest_path = tmp_path / "oversized.json"
    manifest_path.write_bytes(b"secret manifest contents")
    monkeypatch.setattr(
        real_evaluation,
        "MAX_MANIFEST_BYTES",
        8,
        raising=False,
    )

    exit_code = main(["--manifest", str(manifest_path)])
    output = capsys.readouterr()
    report = json.loads(output.out)

    assert exit_code == 2
    assert output.err == ""
    assert report["status"] == "BLOCKED"
    assert report["manifest_schema_valid"] is False
    assert "size limit" in report["validation_errors"][0]
    assert "secret manifest contents" not in output.out


def test_readiness_report_normalizes_json_recursion_error(monkeypatch):
    def fail_parse(*args, **kwargs):
        raise RecursionError("decoder recursion limit")

    monkeypatch.setattr(real_evaluation.json, "loads", fail_parse)

    report = readiness_report("{}")

    assert report["status"] == "BLOCKED"
    assert report["manifest_schema_valid"] is False
    assert report["real_corpus_metrics_produced"] is False
    assert report["validation_errors"]


@pytest.mark.parametrize(
    ("record", "field", "value"),
    [
        ("documents", "rights_review_evidence_ref", ""),
        ("judgments", "reviewer_b_id", "reviewer-a"),
        ("judgments", "reviewer_b_relevant", False),
    ],
)
def test_readiness_report_fails_closed_on_unverified_annotation_fields(
    record, field, value
):
    payload = json.loads(_manifest().to_json())
    payload[record][0][field] = value

    report = readiness_report(json.dumps(payload))

    assert report["status"] == "BLOCKED"
    assert report["manifest_schema_valid"] is False
    assert report["real_corpus_metrics_produced"] is False
    assert report["validation_errors"]


def test_local_readiness_command_reports_blocked_without_metrics(tmp_path, capsys):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(_manifest().to_json(), encoding="utf-8")

    exit_code = main(["--manifest", str(manifest_path)])

    report = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert report["status"] == "BLOCKED"
    assert report["manifest_schema_valid"] is True
    assert report["real_corpus_metrics_produced"] is False


def test_local_readiness_command_missing_manifest_stays_blocked(capsys):
    exit_code = main([])

    report = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert report["status"] == "BLOCKED"
    assert report["manifest_schema_valid"] is False
    assert report["real_corpus_metrics_produced"] is False


def test_local_readiness_command_reports_stdout_write_failure(monkeypatch, capsys):
    class BrokenStdout:
        def write(self, value):
            raise OSError("disk full")

        def flush(self):
            return None

    monkeypatch.setattr(sys, "stdout", BrokenStdout())

    exit_code = main([])

    output = capsys.readouterr()
    assert exit_code == 1
    assert output.out == ""
    assert "could not write readiness report" in output.err.lower()
