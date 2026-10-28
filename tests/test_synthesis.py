from dataclasses import FrozenInstanceError, fields, replace
from uuid import UUID

import pytest

from scientia.evidence import Location
from scientia.synthesis import (
    ResearchQuestion,
    SynthesisFinding,
    SynthesisResult,
    synthesize,
)
from scientia.verification import (
    AssessmentOutcome,
    ClaimAssessment,
    EvidenceObservation,
    EvidenceStance,
    ReviewState,
)

QUESTION_ID = UUID("10000000-0000-4000-8000-000000000001")
ASSESSMENT_ID_1 = UUID("20000000-0000-4000-8000-000000000001")
ASSESSMENT_ID_2 = UUID("20000000-0000-4000-8000-000000000002")
ASSESSMENT_ID_3 = UUID("20000000-0000-4000-8000-000000000003")
CLAIM_ID = UUID("30000000-0000-4000-8000-000000000001")
SOURCE_ID_1 = UUID("40000000-0000-4000-8000-000000000001")
SOURCE_ID_2 = UUID("40000000-0000-4000-8000-000000000002")
PASSAGE_ID_1 = UUID("50000000-0000-4000-8000-000000000001")
PASSAGE_ID_2 = UUID("50000000-0000-4000-8000-000000000002")

QUESTION = ResearchQuestion(
    QUESTION_ID,
    "Does intervention X reduce symptom severity?",
)


def make_observation(
    *,
    passage_id: UUID = PASSAGE_ID_1,
    source_id: UUID = SOURCE_ID_1,
    digest: str | None = "a" * 64,
    location: Location | None = Location(page_start=2, page_end=2),
    text: str = "The measured symptom severity declined.",
    stance: EvidenceStance = EvidenceStance.SUPPORTS,
) -> EvidenceObservation:
    return EvidenceObservation(
        passage_id=passage_id,
        source_id=source_id,
        source_sha256=digest,
        location=location,
        passage_text=text,
        stance=stance,
    )


def make_assessment(
    assessment_id: UUID = ASSESSMENT_ID_1,
    *,
    outcome: AssessmentOutcome | None = AssessmentOutcome.SUPPORTED,
    review_state: ReviewState = ReviewState.HUMAN_REVIEWED,
    evidence: tuple[EvidenceObservation, ...] | None = None,
) -> ClaimAssessment:
    if evidence is None:
        evidence = (make_observation(),)
    return ClaimAssessment(
        assessment_id=assessment_id,
        claim_id=CLAIM_ID,
        claim_text="Intervention X reduces symptom severity.",
        outcome=outcome,
        evidence=evidence,
        review_state=review_state,
    )


def test_research_question_accepts_uuid_and_nonblank_text():
    question = ResearchQuestion(QUESTION_ID, "What is the effect?")

    assert question.question_id == QUESTION_ID
    assert question.text == "What is the effect?"


@pytest.mark.parametrize("text", ["", " \n\t"])
def test_research_question_rejects_blank_text(text):
    with pytest.raises(ValueError, match="text"):
        ResearchQuestion(QUESTION_ID, text)


def test_synthesis_finding_accepts_human_reviewed_assessment_with_outcome():
    assessment = make_assessment()

    finding = SynthesisFinding(assessment)

    assert finding.assessment is assessment
    assert finding.assessment.evidence[0].source_id == SOURCE_ID_1


@pytest.mark.parametrize(
    ("outcome", "review_state"),
    [
        (AssessmentOutcome.SUPPORTED, ReviewState.DRAFT),
        (AssessmentOutcome.SUPPORTED, ReviewState.NEEDS_CLARIFICATION),
        (None, ReviewState.HUMAN_REVIEWED),
    ],
)
def test_nonfinal_assessment_is_kept_unresolved(outcome, review_state):
    assessment = make_assessment(
        outcome=outcome,
        review_state=review_state,
    )

    result = synthesize(QUESTION, (assessment,))

    assert result.findings == ()
    assert result.unresolved_assessments == (assessment,)


def test_only_reviewed_assessments_with_outcome_become_findings():
    reviewed = make_assessment(ASSESSMENT_ID_1)
    draft = make_assessment(
        ASSESSMENT_ID_2,
        review_state=ReviewState.DRAFT,
    )
    unresolved = make_assessment(ASSESSMENT_ID_3, outcome=None)

    result = synthesize(QUESTION, (reviewed, draft, unresolved))

    assert tuple(finding.assessment for finding in result.findings) == (reviewed,)
    assert result.unresolved_assessments == (draft, unresolved)


def test_insufficient_evidence_remains_distinct_from_contradiction():
    insufficient = make_assessment(
        ASSESSMENT_ID_1,
        outcome=AssessmentOutcome.INSUFFICIENT_EVIDENCE,
        evidence=(
            make_observation(
                stance=EvidenceStance.IRRELEVANT,
                text="The passage discusses an unrelated outcome.",
            ),
        ),
    )
    contradicted = make_assessment(
        ASSESSMENT_ID_2,
        outcome=AssessmentOutcome.CONTRADICTED,
        evidence=(
            make_observation(
                passage_id=PASSAGE_ID_2,
                source_id=SOURCE_ID_2,
                stance=EvidenceStance.CONTRADICTS,
                text="No reduction in symptom severity was observed.",
            ),
        ),
    )

    result = synthesize(QUESTION, (insufficient, contradicted))

    assert [finding.assessment.outcome for finding in result.findings] == [
        AssessmentOutcome.INSUFFICIENT_EVIDENCE,
        AssessmentOutcome.CONTRADICTED,
    ]


def test_conflicting_evidence_is_preserved_without_resolving_either_side():
    supporting = make_observation(
        passage_id=PASSAGE_ID_1,
        source_id=SOURCE_ID_1,
        stance=EvidenceStance.SUPPORTS,
    )
    contradicting = make_observation(
        passage_id=PASSAGE_ID_2,
        source_id=SOURCE_ID_2,
        stance=EvidenceStance.CONTRADICTS,
        text="A second study found no symptom reduction.",
    )
    conflicting = make_assessment(
        outcome=AssessmentOutcome.CONFLICTING,
        evidence=(supporting, contradicting),
    )

    result = synthesize(QUESTION, (conflicting,))

    assert result.findings[0].assessment is conflicting
    assert result.findings[0].assessment.evidence == (supporting, contradicting)
    assert tuple(item.stance for item in result.findings[0].assessment.evidence) == (
        EvidenceStance.SUPPORTS,
        EvidenceStance.CONTRADICTS,
    )


def test_multiple_sources_and_full_provenance_are_preserved():
    first = make_observation(
        passage_id=PASSAGE_ID_1,
        source_id=SOURCE_ID_1,
        digest="a" * 64,
        location=Location(page_start=2, page_end=2),
        text="  Source one reports a decrease.  ",
    )
    second = make_observation(
        passage_id=PASSAGE_ID_2,
        source_id=SOURCE_ID_2,
        digest="b" * 64,
        location=Location(section_path=("Results", "Primary outcome")),
        text="Source two reports a decrease.",
    )
    assessment = make_assessment(evidence=(first, second))

    result = synthesize(QUESTION, (assessment,))
    preserved = result.findings[0].assessment.evidence

    assert preserved == (first, second)
    assert preserved[0].source_id == SOURCE_ID_1
    assert preserved[0].passage_id == PASSAGE_ID_1
    assert preserved[0].source_sha256 == "a" * 64
    assert preserved[0].location == Location(page_start=2, page_end=2)
    assert preserved[0].passage_text == "  Source one reports a decrease.  "
    assert preserved[1].source_id == SOURCE_ID_2
    assert preserved[1].passage_id == PASSAGE_ID_2
    assert preserved[1].source_sha256 == "b" * 64
    assert preserved[1].location == Location(
        section_path=("Results", "Primary outcome")
    )


def test_opposing_assessments_for_same_claim_remain_separate():
    supported = make_assessment(
        ASSESSMENT_ID_1,
        outcome=AssessmentOutcome.SUPPORTED,
    )
    contradicted = make_assessment(
        ASSESSMENT_ID_2,
        outcome=AssessmentOutcome.CONTRADICTED,
        evidence=(
            make_observation(
                passage_id=PASSAGE_ID_2,
                source_id=SOURCE_ID_2,
                stance=EvidenceStance.CONTRADICTS,
            ),
        ),
    )

    result = synthesize(QUESTION, (supported, contradicted))

    assert len(result.findings) == 2
    assert [finding.assessment.assessment_id for finding in result.findings] == [
        ASSESSMENT_ID_1,
        ASSESSMENT_ID_2,
    ]
    assert {finding.assessment.claim_id for finding in result.findings} == {CLAIM_ID}


def test_synthesis_rejects_same_claim_id_with_different_claim_text():
    first = make_assessment(ASSESSMENT_ID_1)
    second = replace(
        make_assessment(ASSESSMENT_ID_2),
        claim_text="The treatment increases symptoms.",
    )

    with pytest.raises(ValueError, match="claim_id.*claim_text"):
        synthesize(QUESTION, (first, second))


def test_synthesis_rejects_duplicate_assessment_ids():
    assessment = make_assessment(ASSESSMENT_ID_1)

    with pytest.raises(ValueError, match="duplicate assessment_id"):
        synthesize(QUESTION, (assessment, assessment))


def test_findings_and_unresolved_assessments_preserve_relative_input_order():
    first = make_assessment(ASSESSMENT_ID_1)
    draft = make_assessment(
        ASSESSMENT_ID_2,
        review_state=ReviewState.NEEDS_CLARIFICATION,
    )
    third = make_assessment(
        ASSESSMENT_ID_3,
        outcome=AssessmentOutcome.CONTRADICTED,
        evidence=(
            make_observation(
                passage_id=PASSAGE_ID_2,
                source_id=SOURCE_ID_2,
                stance=EvidenceStance.CONTRADICTS,
            ),
        ),
    )

    expected_findings = (
        SynthesisFinding(first),
        SynthesisFinding(third),
    )
    expected_unresolved = (draft,)

    assert synthesize(QUESTION, (first, draft, third)) == SynthesisResult(
        QUESTION,
        expected_findings,
        expected_unresolved,
    )
    assert synthesize(QUESTION, (first, draft, third)) == synthesize(
        QUESTION,
        (first, draft, third),
    )


@pytest.mark.parametrize(
    ("question", "assessments"),
    [
        ("not a question record", ()),
        (QUESTION, ("not an assessment",)),
        (QUESTION, None),
        (None, ()),
    ],
)
def test_synthesize_rejects_invalid_input_types(question, assessments):
    with pytest.raises(TypeError):
        synthesize(question, assessments)


@pytest.mark.parametrize(
    "assessment",
    [
        "not an assessment",
        None,
    ],
)
def test_synthesis_finding_rejects_invalid_assessment_type(assessment):
    with pytest.raises(TypeError, match="ClaimAssessment"):
        SynthesisFinding(assessment)


@pytest.mark.parametrize(
    "assessment",
    [
        make_assessment(review_state=ReviewState.DRAFT),
        make_assessment(outcome=None),
    ],
)
def test_synthesis_finding_rejects_unreviewed_or_unresolved_assessment(assessment):
    with pytest.raises(ValueError, match="HUMAN_REVIEWED|outcome"):
        SynthesisFinding(assessment)


def test_synthesis_result_rejects_mutable_or_malformed_collections():
    finding = SynthesisFinding(make_assessment())

    with pytest.raises(TypeError, match="tuple"):
        SynthesisResult(QUESTION, [finding], ())
    with pytest.raises(TypeError, match="SynthesisFinding"):
        SynthesisResult(QUESTION, ("not a finding",), ())
    with pytest.raises(TypeError, match="tuple"):
        SynthesisResult(QUESTION, (), [])
    with pytest.raises(TypeError, match="ClaimAssessment"):
        SynthesisResult(QUESTION, (), ("not an assessment",))


def test_synthesis_result_rejects_completed_assessment_as_unresolved():
    completed = make_assessment()

    with pytest.raises(ValueError, match="unresolved"):
        SynthesisResult(QUESTION, (), (completed,))


def test_synthesis_does_not_expose_retrieval_score_or_rank():
    finding_fields = {field.name for field in fields(SynthesisFinding)}
    result_fields = {field.name for field in fields(SynthesisResult)}

    assert "score" not in finding_fields | result_fields
    assert "rank" not in finding_fields | result_fields


def test_synthesis_records_and_result_tuples_are_immutable():
    assessment = make_assessment()
    finding = SynthesisFinding(assessment)
    result = SynthesisResult(QUESTION, (finding,), ())

    with pytest.raises(FrozenInstanceError):
        QUESTION.text = "Changed?"
    with pytest.raises(FrozenInstanceError):
        finding.assessment = make_assessment(ASSESSMENT_ID_2)
    with pytest.raises(FrozenInstanceError):
        result.question = ResearchQuestion(QUESTION_ID, "Changed?")
    assert isinstance(result.findings, tuple)
    assert isinstance(result.unresolved_assessments, tuple)
