from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
from uuid import UUID

import pytest

from scientia.evidence import Location
from scientia.pdf_ingestion import PdfIngestionError
from scientia.retrieval import RetrievalHit
from scientia.synthesis import ResearchQuestion, SynthesisFinding, SynthesisResult
from scientia.verification import (
    AssessmentOutcome,
    ClaimAssessment,
    EvidenceObservation,
    EvidenceStance,
    ReviewState,
)
from scientia.workflow import (
    PreparedResearch,
    ResearchWorkflowResult,
    finalize_research,
    prepare_research,
)

QUESTION_ID = UUID("11000000-0000-4000-8000-000000000001")
CLAIM_ID = UUID("22000000-0000-4000-8000-000000000001")
ASSESSMENT_ID_1 = UUID("33000000-0000-4000-8000-000000000001")
ASSESSMENT_ID_2 = UUID("33000000-0000-4000-8000-000000000002")
ASSESSMENT_ID_3 = UUID("33000000-0000-4000-8000-000000000003")
ASSESSMENT_ID_4 = UUID("33000000-0000-4000-8000-000000000004")
ASSESSMENT_ID_5 = UUID("33000000-0000-4000-8000-000000000005")


def _pdf_bytes(pages: list[str], title: str | None = None) -> bytes:
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    ]
    page_ids = [3 + index * 2 for index in range(len(pages))]
    content_ids = [page_id + 1 for page_id in page_ids]
    kids = b" ".join(f"{page_id} 0 R".encode() for page_id in page_ids)
    objects[1] = (
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
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
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


def _write_pdf(path: Path, pages: list[str], title: str | None = None) -> bytes:
    contents = _pdf_bytes(pages, title)
    path.write_bytes(contents)
    return contents


def _assessment(
    assessment_id: UUID,
    observation: EvidenceObservation,
    *,
    outcome: AssessmentOutcome | None = AssessmentOutcome.SUPPORTED,
    review_state: ReviewState = ReviewState.HUMAN_REVIEWED,
) -> ClaimAssessment:
    return ClaimAssessment(
        assessment_id=assessment_id,
        claim_id=CLAIM_ID,
        claim_text="Intervention X reduces symptoms.",
        outcome=outcome,
        evidence=(observation,),
        review_state=review_state,
    )


def test_prepares_one_pdf_and_retrieves_using_exact_question_text(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "trial.pdf"
    contents = _write_pdf(
        path,
        ["Intervention X reduced symptom severity."],
        title="Trial report",
    )
    question = ResearchQuestion(
        QUESTION_ID,
        "Intervention symptom",
    )
    from scientia import workflow

    real_retrieve = workflow.retrieve
    received_queries: list[str] = []

    def capture_query(query, passages, limit=10):
        received_queries.append(query)
        return real_retrieve(query, passages, limit)

    monkeypatch.setattr(workflow, "retrieve", capture_query)
    result = prepare_research(question, (path,))

    assert result.question is question
    assert received_queries == ["Intervention symptom"]
    assert len(result.ingestion_results) == 1
    assert result.ingestion_results[0].source.title == "Trial report"
    assert result.ingestion_results[0].source.content_sha256 == sha256(
        contents
    ).hexdigest()
    assert result.retrieval_hits == (
        RetrievalHit(result.ingestion_results[0].passages[0], 2),
    )


def test_prepares_multiple_pdfs_in_input_order_and_flattens_passages(
    tmp_path,
):
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    first_bytes = _write_pdf(first, ["Intervention reduces symptom severity."])
    second_bytes = _write_pdf(second, ["Intervention may alter outcomes."])

    result = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptom severity"),
        (first, second),
    )

    assert [item.original_filename for item in result.ingestion_results] == [
        "first.pdf",
        "second.pdf",
    ]
    assert [
        hit.passage.source_id for hit in result.retrieval_hits
    ] == [
        result.ingestion_results[0].source.source_id,
        result.ingestion_results[1].source.source_id,
    ]
    assert [
        result.ingestion_results[0].source.content_sha256,
        result.ingestion_results[1].source.content_sha256,
    ] == [sha256(first_bytes).hexdigest(), sha256(second_bytes).hexdigest()]


def test_rejects_unbounded_pdf_batches_before_ingesting_inputs(tmp_path):
    question = ResearchQuestion(QUESTION_ID, "research question")
    pdf_paths = tuple(tmp_path / f"paper-{index}.pdf" for index in range(9))

    with pytest.raises(PdfIngestionError, match="PDF count limit") as error:
        prepare_research(question, pdf_paths)

    assert error.value.stage == "validate"


def test_rejects_duplicate_pdf_paths_before_ingesting_inputs(tmp_path):
    path = tmp_path / "paper.pdf"
    _write_pdf(path, ["Intervention reduced symptoms."])
    path_alias = tmp_path / "paper-alias.pdf"
    path_alias.symlink_to(path)
    question = ResearchQuestion(QUESTION_ID, "Intervention symptoms")

    with pytest.raises(PdfIngestionError, match="Duplicate PDF input") as error:
        prepare_research(question, (path, path_alias))

    assert error.value.stage == "validate"
    assert str(path) not in str(error.value)


def test_rejects_byte_identical_pdf_inputs_at_different_paths(tmp_path):
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    contents = _write_pdf(first, ["Intervention reduced symptoms."])
    second.write_bytes(contents)
    question = ResearchQuestion(QUESTION_ID, "Intervention symptoms")

    with pytest.raises(PdfIngestionError, match="Duplicate PDF content") as error:
        prepare_research(question, (first, second))

    assert error.value.stage == "validate"


def test_prepare_research_is_deterministic_for_fixed_local_pdf(tmp_path):
    path = tmp_path / "fixed.pdf"
    _write_pdf(path, ["Intervention reduces symptoms.", "Other outcome."])
    question = ResearchQuestion(QUESTION_ID, "Intervention symptoms")

    first = prepare_research(question, (path,))
    second = prepare_research(question, (path,))

    assert [item.source.content_sha256 for item in first.ingestion_results] == [
        item.source.content_sha256 for item in second.ingestion_results
    ]
    assert [passage.text for passage in first.ingestion_results[0].passages] == [
        passage.text for passage in second.ingestion_results[0].passages
    ]
    assert [
        (hit.passage.text, hit.score, hit.passage.location)
        for hit in first.retrieval_hits
    ] == [
        (hit.passage.text, hit.score, hit.passage.location)
        for hit in second.retrieval_hits
    ]


def test_empty_retrieval_is_valid_and_does_not_create_assessments(tmp_path):
    path = tmp_path / "unrelated.pdf"
    _write_pdf(path, ["A telescope observed distant galaxies."])

    result = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )

    assert result.retrieval_hits == ()
    assert result.ingestion_results[0].passages


def test_invalid_pdf_fails_without_returning_partial_preparation(tmp_path):
    valid = tmp_path / "valid.pdf"
    invalid = tmp_path / "invalid.pdf"
    _write_pdf(valid, ["Valid first paper."])
    invalid.write_bytes(b"not a PDF")

    with pytest.raises(PdfIngestionError):
        prepare_research(
            ResearchQuestion(QUESTION_ID, "paper"),
            (valid, invalid),
        )


def test_finalize_preserves_full_provenance_from_pdf_to_finding(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduced symptoms."])
    question = ResearchQuestion(QUESTION_ID, "Intervention symptoms")
    prepared = prepare_research(question, (path,))
    source = prepared.ingestion_results[0].source
    passage = prepared.ingestion_results[0].passages[0]
    observation = EvidenceObservation.from_source_passage(
        source,
        passage,
        EvidenceStance.SUPPORTS,
    )
    assessment = _assessment(ASSESSMENT_ID_1, observation)

    result = finalize_research(prepared, (assessment,))
    preserved = result.synthesis.findings[0].assessment.evidence[0]

    assert result.prepared is prepared
    assert result.assessments == (assessment,)
    assert preserved.source_id == source.source_id
    assert preserved.passage_id == passage.passage_id
    assert preserved.source_sha256 == sha256(path.read_bytes()).hexdigest()
    assert preserved.location == passage.location
    assert preserved.passage_text == passage.text


def test_finalize_accepts_valid_ingested_passage_not_in_retrieval_hits(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms.", "Unmatched endpoint."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    source = prepared.ingestion_results[0].source
    non_hit = prepared.ingestion_results[0].passages[1]
    assert all(
        hit.passage.passage_id != non_hit.passage_id
        for hit in prepared.retrieval_hits
    )
    observation = EvidenceObservation.from_source_passage(
        source,
        non_hit,
        EvidenceStance.UNCLEAR,
    )

    result = finalize_research(
        prepared,
        (
            _assessment(
                ASSESSMENT_ID_1,
                observation,
                outcome=AssessmentOutcome.INSUFFICIENT_EVIDENCE,
            ),
        ),
    )

    assert result.synthesis.findings[0].assessment.evidence[0].passage_id == (
        non_hit.passage_id
    )


def test_finalize_rejects_unknown_source_id(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    passage = prepared.ingestion_results[0].passages[0]
    observation = EvidenceObservation(
        passage_id=passage.passage_id,
        source_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        source_sha256=prepared.ingestion_results[0].source.content_sha256,
        location=passage.location,
        passage_text=passage.text,
        stance=EvidenceStance.SUPPORTS,
    )

    with pytest.raises(ValueError, match="source|passage"):
        finalize_research(prepared, (_assessment(ASSESSMENT_ID_1, observation),))


def test_finalize_rejects_unknown_passage_id(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    source = prepared.ingestion_results[0].source
    observation = EvidenceObservation(
        passage_id=UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"),
        source_id=source.source_id,
        source_sha256=source.content_sha256,
        location=Location(page_start=1, page_end=1),
        passage_text="Intervention reduces symptoms.",
        stance=EvidenceStance.SUPPORTS,
    )

    with pytest.raises(ValueError, match="passage"):
        finalize_research(prepared, (_assessment(ASSESSMENT_ID_1, observation),))


@pytest.mark.parametrize(
    ("field", "altered_value"),
    [
        ("source_sha256", "b" * 64),
        ("source_sha256", None),
        ("location", Location(page_start=99, page_end=99)),
        ("passage_text", "Altered evidence text."),
    ],
)
def test_finalize_rejects_altered_provenance(tmp_path, field, altered_value):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    source = prepared.ingestion_results[0].source
    passage = prepared.ingestion_results[0].passages[0]
    original = EvidenceObservation.from_source_passage(
        source,
        passage,
        EvidenceStance.SUPPORTS,
    )
    changed = replace(original, **{field: altered_value})

    with pytest.raises(ValueError, match="provenance|match|does not"):
        finalize_research(prepared, (_assessment(ASSESSMENT_ID_1, changed),))


def test_finalize_keeps_unresolved_insufficient_and_conflicting_assessments_distinct(
    tmp_path,
):
    path = tmp_path / "study.pdf"
    _write_pdf(
        path,
        ["Intervention reduced symptoms.", "No reduction was observed."],
    )
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    source = prepared.ingestion_results[0].source
    first_passage, second_passage = prepared.ingestion_results[0].passages
    support = EvidenceObservation.from_source_passage(
        source,
        first_passage,
        EvidenceStance.SUPPORTS,
    )
    contradiction = EvidenceObservation.from_source_passage(
        source,
        second_passage,
        EvidenceStance.CONTRADICTS,
    )
    draft = _assessment(
        ASSESSMENT_ID_1,
        support,
        review_state=ReviewState.DRAFT,
    )
    clarification = _assessment(
        ASSESSMENT_ID_4,
        support,
        review_state=ReviewState.NEEDS_CLARIFICATION,
    )
    no_outcome = _assessment(
        ASSESSMENT_ID_5,
        support,
        outcome=None,
    )
    insufficient = ClaimAssessment(
        assessment_id=ASSESSMENT_ID_2,
        claim_id=CLAIM_ID,
        claim_text="Intervention X reduces symptoms.",
        outcome=AssessmentOutcome.INSUFFICIENT_EVIDENCE,
        evidence=(
            EvidenceObservation.from_source_passage(
                source,
                first_passage,
                EvidenceStance.UNCLEAR,
            ),
        ),
        review_state=ReviewState.HUMAN_REVIEWED,
    )
    conflicting = ClaimAssessment(
        assessment_id=ASSESSMENT_ID_3,
        claim_id=CLAIM_ID,
        claim_text="Intervention X reduces symptoms.",
        outcome=AssessmentOutcome.CONFLICTING,
        evidence=(support, contradiction),
        review_state=ReviewState.HUMAN_REVIEWED,
    )

    result = finalize_research(
        prepared,
        (draft, clarification, no_outcome, insufficient, conflicting),
    )

    assert result.synthesis.unresolved_assessments == (
        draft,
        clarification,
        no_outcome,
    )
    assert [
        finding.assessment.outcome for finding in result.synthesis.findings
    ] == [
        AssessmentOutcome.INSUFFICIENT_EVIDENCE,
        AssessmentOutcome.CONFLICTING,
    ]
    assert result.synthesis.findings[1].assessment.evidence == (
        support,
        contradiction,
    )


def test_retrieval_scores_do_not_determine_claim_assessment_outcome(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention symptom intervention symptom"])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptom"),
        (path,),
    )
    assert prepared.retrieval_hits[0].score == 2
    passage = prepared.ingestion_results[0].passages[0]
    observation = EvidenceObservation.from_source_passage(
        prepared.ingestion_results[0].source,
        passage,
        EvidenceStance.UNCLEAR,
    )
    assessment = _assessment(
        ASSESSMENT_ID_1,
        observation,
        outcome=None,
        review_state=ReviewState.DRAFT,
    )

    result = finalize_research(prepared, (assessment,))

    assert result.synthesis.findings == ()
    assert result.synthesis.unresolved_assessments == (assessment,)


@pytest.mark.parametrize(
    ("question", "pdf_paths", "limit"),
    [
        ("not a question", (), 10),
        (None, (), 10),
        (ResearchQuestion(QUESTION_ID, "Question?"), "not-a-sequence.pdf", 10),
        (ResearchQuestion(QUESTION_ID, "Question?"), (42,), 10),
        (ResearchQuestion(QUESTION_ID, "Question?"), (), 0),
        (ResearchQuestion(QUESTION_ID, "Question?"), (), True),
        (ResearchQuestion(QUESTION_ID, "Question?"), (), 1.5),
    ],
)
def test_prepare_research_rejects_invalid_inputs(question, pdf_paths, limit):
    with pytest.raises((TypeError, ValueError)):
        prepare_research(question, pdf_paths, limit=limit)


@pytest.mark.parametrize(
    ("prepared", "assessments"),
    [
        ("not prepared research", ()),
        (None, ()),
        (None, ("not an assessment",)),
    ],
)
def test_finalize_rejects_invalid_inputs(prepared, assessments):
    with pytest.raises(TypeError):
        finalize_research(prepared, assessments)


def test_prepared_and_final_workflow_records_are_immutable(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    result = finalize_research(prepared, ())

    assert isinstance(prepared.ingestion_results, tuple)
    assert isinstance(prepared.retrieval_hits, tuple)
    assert isinstance(result.assessments, tuple)
    with pytest.raises(FrozenInstanceError):
        prepared.question = ResearchQuestion(QUESTION_ID, "Changed?")
    with pytest.raises(FrozenInstanceError):
        result.prepared = prepared
    assert result.synthesis.findings == ()


def test_repeated_finalization_is_deterministic_for_fixed_assessments(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    source = prepared.ingestion_results[0].source
    passage = prepared.ingestion_results[0].passages[0]
    assessment = _assessment(
        ASSESSMENT_ID_1,
        EvidenceObservation.from_source_passage(
            source,
            passage,
            EvidenceStance.SUPPORTS,
        ),
    )

    first = finalize_research(prepared, (assessment,))
    second = finalize_research(prepared, (assessment,))

    assert first == second
    assert first.synthesis.findings == (SynthesisFinding(assessment),)


def test_empty_pdf_path_collection_produces_empty_research_result():
    question = ResearchQuestion(QUESTION_ID, "Intervention symptoms")

    result = prepare_research(question, ())

    assert result.question is question
    assert result.ingestion_results == ()
    assert result.retrieval_hits == ()


@pytest.mark.parametrize(
    "passage_change",
    [
        {"passage_id": UUID("44000000-0000-4000-8000-000000000001")},
        {"text": "Altered passage snapshot."},
        {"location": Location(page_start=2, page_end=2)},
    ],
    ids=("unknown-passage-id", "altered-text", "altered-location"),
)
def test_prepared_research_rejects_hits_not_matching_ingested_passages(
    tmp_path,
    passage_change,
):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    original_hit = prepared.retrieval_hits[0]
    altered_hit = replace(
        original_hit,
        passage=replace(original_hit.passage, **passage_change),
    )

    with pytest.raises(ValueError, match="retrieval hit"):
        PreparedResearch(
            prepared.question,
            prepared.ingestion_results,
            (altered_hit,),
        )


def test_prepared_research_accepts_equivalent_ingested_passage_value(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    original_hit = prepared.retrieval_hits[0]
    equivalent_hit = replace(
        original_hit,
        passage=replace(original_hit.passage),
    )

    result = PreparedResearch(
        prepared.question,
        prepared.ingestion_results,
        (equivalent_hit,),
    )

    assert result.retrieval_hits == (equivalent_hit,)


def test_prepared_research_rejects_forged_retrieval_score(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    forged_hit = replace(prepared.retrieval_hits[0], score=100)

    with pytest.raises(ValueError, match="ranked results"):
        PreparedResearch(
            prepared.question,
            prepared.ingestion_results,
            (forged_hit,),
        )


def test_prepared_research_rejects_reordered_retrieval_hits(tmp_path):
    path = tmp_path / "study.pdf"
    _write_pdf(
        path,
        ["Intervention reduces symptoms.", "Intervention may alter outcomes."],
    )
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    reversed_hits = tuple(reversed(prepared.retrieval_hits))

    with pytest.raises(ValueError, match="ranked results"):
        PreparedResearch(
            prepared.question,
            prepared.ingestion_results,
            reversed_hits,
        )


def test_research_workflow_result_rejects_a_different_synthesis_question(
    tmp_path,
):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    other_question = ResearchQuestion(
        UUID("11000000-0000-4000-8000-000000000002"),
        "Different question",
    )

    with pytest.raises(ValueError, match="synthesis question"):
        ResearchWorkflowResult(
            prepared,
            (),
            SynthesisResult(other_question, (), ()),
        )


@pytest.mark.parametrize(
    ("finding_ids", "include_draft"),
    [
        ((ASSESSMENT_ID_1,), True),
        (
            (ASSESSMENT_ID_1, ASSESSMENT_ID_1, ASSESSMENT_ID_2),
            True,
        ),
        ((ASSESSMENT_ID_2, ASSESSMENT_ID_1), True),
        ((ASSESSMENT_ID_1, ASSESSMENT_ID_2), False),
    ],
    ids=(
        "missing-finding",
        "duplicated-finding",
        "reordered-findings",
        "missing-unresolved",
    ),
)
def test_research_workflow_result_rejects_inconsistent_assessment_partition(
    tmp_path,
    finding_ids,
    include_draft,
):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    passage = prepared.ingestion_results[0].passages[0]
    source = prepared.ingestion_results[0].source
    observation = EvidenceObservation.from_source_passage(
        source,
        passage,
        EvidenceStance.SUPPORTS,
    )
    first = _assessment(ASSESSMENT_ID_1, observation)
    second = _assessment(ASSESSMENT_ID_2, observation)
    draft = _assessment(
        ASSESSMENT_ID_3,
        observation,
        outcome=None,
        review_state=ReviewState.DRAFT,
    )
    assessments = (first, draft, second)
    finding_by_id = {
        assessment.assessment_id: SynthesisFinding(assessment)
        for assessment in (first, second)
    }
    with pytest.raises(ValueError, match="assessment"):
        synthesis = SynthesisResult(
            prepared.question,
            tuple(finding_by_id[item] for item in finding_ids),
            (draft,) if include_draft else (),
        )
        ResearchWorkflowResult(prepared, assessments, synthesis)


def test_research_workflow_result_accepts_the_complete_ordered_partition(
    tmp_path,
):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    passage = prepared.ingestion_results[0].passages[0]
    observation = EvidenceObservation.from_source_passage(
        prepared.ingestion_results[0].source,
        passage,
        EvidenceStance.SUPPORTS,
    )
    finding_assessment = _assessment(ASSESSMENT_ID_1, observation)
    unresolved_assessment = _assessment(
        ASSESSMENT_ID_2,
        observation,
        outcome=None,
        review_state=ReviewState.DRAFT,
    )
    assessments = (finding_assessment, unresolved_assessment)

    result = ResearchWorkflowResult(
        prepared,
        assessments,
        SynthesisResult(
            prepared.question,
            (SynthesisFinding(finding_assessment),),
            (unresolved_assessment,),
        ),
    )

    assert result.assessments == assessments
    assert result.synthesis.findings[0].assessment is finding_assessment
    assert result.synthesis.unresolved_assessments == (unresolved_assessment,)


def test_workflow_result_rejects_direct_construction_with_unknown_evidence(
    tmp_path,
):
    path = tmp_path / "study.pdf"
    _write_pdf(path, ["Intervention reduces symptoms."])
    prepared = prepare_research(
        ResearchQuestion(QUESTION_ID, "Intervention symptoms"),
        (path,),
    )
    source = prepared.ingestion_results[0].source
    invalid_observation = EvidenceObservation(
        passage_id=UUID("44000000-0000-4000-8000-000000000099"),
        source_id=source.source_id,
        source_sha256=source.content_sha256,
        location=Location(page_start=1, page_end=1),
        passage_text="Unseen passage claims the intervention works.",
        stance=EvidenceStance.SUPPORTS,
    )
    assessment = _assessment(ASSESSMENT_ID_1, invalid_observation)

    with pytest.raises(ValueError, match="unknown passage"):
        ResearchWorkflowResult(
            prepared,
            (assessment,),
            SynthesisResult(
                prepared.question,
                (SynthesisFinding(assessment),),
                (),
            ),
        )
