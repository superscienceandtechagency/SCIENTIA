from dataclasses import FrozenInstanceError, fields
from uuid import UUID

import pytest

from scientia.evidence import Location, Passage, Source
from scientia.verification import (
    AssessmentOutcome,
    Claim,
    ClaimAssessment,
    EvidenceObservation,
    EvidenceStance,
    ReviewState,
)

CLAIM_ID = UUID("11111111-1111-4111-8111-111111111111")
ASSESSMENT_ID = UUID("22222222-2222-4222-8222-222222222222")
SOURCE_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_SOURCE_ID = UUID("44444444-4444-4444-8444-444444444444")
PASSAGE_ID = UUID("55555555-5555-4555-8555-555555555555")
OTHER_PASSAGE_ID = UUID("66666666-6666-4666-8666-666666666666")
SOURCE_SHA256 = "a" * 64


def make_source(*, content_sha256: str | None = SOURCE_SHA256) -> Source:
    return Source(source_id=SOURCE_ID, content_sha256=content_sha256)


def make_passage(
    *,
    source_id: UUID = SOURCE_ID,
    passage_id: UUID = PASSAGE_ID,
    text: str = "Treatment reduced symptoms in the study group.",
    location: Location | None = Location(page_start=3, page_end=3),
) -> Passage:
    return Passage(
        passage_id=passage_id,
        source_id=source_id,
        text=text,
        location=location,
    )


def make_observation(
    stance: EvidenceStance,
    *,
    passage: Passage | None = None,
    source: Source | None = None,
    reviewer_note: str | None = None,
) -> EvidenceObservation:
    return EvidenceObservation.from_source_passage(
        source or make_source(),
        passage or make_passage(),
        stance,
        reviewer_note=reviewer_note,
    )


def make_assessment(
    outcome: AssessmentOutcome | None,
    observations: tuple[EvidenceObservation, ...] = (),
    *,
    review_state: ReviewState = ReviewState.HUMAN_REVIEWED,
) -> ClaimAssessment:
    return ClaimAssessment(
        assessment_id=ASSESSMENT_ID,
        claim_id=CLAIM_ID,
        claim_text="The treatment reduces symptoms.",
        outcome=outcome,
        evidence=observations,
        review_state=review_state,
    )


def test_supported_assessment_preserves_exact_provenance_snapshots():
    source = make_source()
    location = Location(page_start=3, page_end=4, section_path=("Results",))
    text = "  Treatment reduced symptoms in the study group.  "
    passage = make_passage(text=text, location=location)
    observation = EvidenceObservation.from_source_passage(
        source,
        passage,
        EvidenceStance.SUPPORTS,
        reviewer_note="The passage reports a reduction.",
    )
    claim = Claim(CLAIM_ID, "The treatment reduces symptoms.")
    assessment = ClaimAssessment(
        assessment_id=ASSESSMENT_ID,
        claim_id=claim.claim_id,
        claim_text=claim.text,
        outcome=AssessmentOutcome.SUPPORTED,
        evidence=(observation,),
        review_state=ReviewState.HUMAN_REVIEWED,
    )

    assert assessment.claim_text == claim.text
    assert observation.passage_id == PASSAGE_ID
    assert observation.source_id == SOURCE_ID
    assert observation.source_sha256 == SOURCE_SHA256
    assert observation.location is location
    assert observation.passage_text == text
    assert observation.stance is EvidenceStance.SUPPORTS
    assert observation.reviewer_note == "The passage reports a reduction."


def test_contradicted_assessment_requires_and_preserves_contradicting_evidence():
    observation = make_observation(EvidenceStance.CONTRADICTS)

    assessment = make_assessment(
        AssessmentOutcome.CONTRADICTED,
        (observation,),
    )

    assert assessment.outcome is AssessmentOutcome.CONTRADICTED
    assert assessment.evidence == (observation,)


def test_irrelevant_evidence_can_be_assessed_as_insufficient_not_contradictory():
    observation = make_observation(EvidenceStance.IRRELEVANT)

    assessment = make_assessment(
        AssessmentOutcome.INSUFFICIENT_EVIDENCE,
        (observation,),
    )

    assert assessment.outcome is AssessmentOutcome.INSUFFICIENT_EVIDENCE
    assert assessment.evidence[0].stance is EvidenceStance.IRRELEVANT


def test_conflicting_assessment_requires_support_and_contradiction():
    supporting = make_observation(EvidenceStance.SUPPORTS)
    contradicting = make_observation(
        EvidenceStance.CONTRADICTS,
        passage=make_passage(
            passage_id=OTHER_PASSAGE_ID,
            text="Treatment did not reduce symptoms.",
        ),
    )

    assessment = make_assessment(
        AssessmentOutcome.CONFLICTING,
        (supporting, contradicting),
    )

    assert assessment.evidence == (supporting, contradicting)


def test_assessment_rejects_same_passage_as_supporting_and_contradicting():
    passage = make_passage()
    supporting = make_observation(
        EvidenceStance.SUPPORTS,
        passage=passage,
    )
    contradicting = make_observation(
        EvidenceStance.CONTRADICTS,
        passage=passage,
    )

    with pytest.raises(ValueError, match="duplicate evidence passage"):
        make_assessment(
            AssessmentOutcome.CONFLICTING,
            (supporting, contradicting),
        )


@pytest.mark.parametrize(
    "outcome",
    [AssessmentOutcome.SUPPORTED, AssessmentOutcome.CONTRADICTED],
)
def test_mixed_support_and_contradiction_reject_one_sided_outcomes(outcome):
    supporting = make_observation(EvidenceStance.SUPPORTS)
    contradicting = make_observation(
        EvidenceStance.CONTRADICTS,
        passage=make_passage(
            passage_id=OTHER_PASSAGE_ID,
            text="Treatment did not reduce symptoms.",
        ),
    )

    with pytest.raises(ValueError, match="conflicting|both"):
        make_assessment(outcome, (supporting, contradicting))


def test_mixed_support_and_contradiction_accept_conflicting_outcome_unchanged():
    supporting = make_observation(EvidenceStance.SUPPORTS)
    contradicting = make_observation(
        EvidenceStance.CONTRADICTS,
        passage=make_passage(
            passage_id=OTHER_PASSAGE_ID,
            text="Treatment did not reduce symptoms.",
        ),
    )

    assessment = make_assessment(
        AssessmentOutcome.CONFLICTING,
        (supporting, contradicting),
    )

    assert assessment.outcome is AssessmentOutcome.CONFLICTING
    assert assessment.evidence == (supporting, contradicting)


def test_insufficient_evidence_rejects_mixed_support_and_contradiction():
    supporting = make_observation(EvidenceStance.SUPPORTS)
    contradicting = make_observation(
        EvidenceStance.CONTRADICTS,
        passage=make_passage(
            passage_id=OTHER_PASSAGE_ID,
            text="Treatment did not reduce symptoms.",
        ),
    )

    with pytest.raises(ValueError, match="mixed supporting and contradicting"):
        make_assessment(
            AssessmentOutcome.INSUFFICIENT_EVIDENCE,
            (supporting, contradicting),
        )


@pytest.mark.parametrize(
    "review_state",
    [ReviewState.DRAFT, ReviewState.NEEDS_CLARIFICATION],
)
def test_unresolved_assessments_allow_no_outcome(review_state):
    assessment = make_assessment(None, review_state=review_state)

    assert assessment.outcome is None
    assert assessment.review_state is review_state


def test_observation_factory_rejects_mismatched_source_and_passage():
    with pytest.raises(ValueError, match="source"):
        EvidenceObservation.from_source_passage(
            make_source(),
            make_passage(source_id=OTHER_SOURCE_ID),
            EvidenceStance.SUPPORTS,
        )


def test_observation_preserves_missing_hash_and_location_as_none():
    source = make_source(content_sha256=None)
    passage = make_passage(location=None)

    observation = EvidenceObservation.from_source_passage(
        source,
        passage,
        EvidenceStance.UNCLEAR,
    )

    assert observation.source_sha256 is None
    assert observation.location is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("passage_id", "not-a-uuid"),
        ("source_id", "not-a-uuid"),
    ],
)
def test_observation_rejects_malformed_uuid_fields(field, value):
    kwargs = {
        "passage_id": PASSAGE_ID,
        "source_id": SOURCE_ID,
        "source_sha256": SOURCE_SHA256,
        "location": None,
        "passage_text": "Evidence text.",
        "stance": EvidenceStance.SUPPORTS,
    }
    kwargs[field] = value

    with pytest.raises(TypeError, match="UUID"):
        EvidenceObservation(**kwargs)


@pytest.mark.parametrize("digest", ["A" * 64, "g" * 64, "a" * 63])
def test_observation_rejects_malformed_hash(digest):
    with pytest.raises(ValueError, match="64 lowercase hexadecimal"):
        EvidenceObservation(
            passage_id=PASSAGE_ID,
            source_id=SOURCE_ID,
            source_sha256=digest,
            location=None,
            passage_text="Evidence text.",
            stance=EvidenceStance.SUPPORTS,
        )


@pytest.mark.parametrize(
    "claim_id",
    ["not-a-uuid", None],
)
def test_claim_rejects_malformed_uuid(claim_id):
    with pytest.raises(TypeError, match="claim_id"):
        Claim(claim_id, "A declarative claim.")


@pytest.mark.parametrize("text", ["", " \n\t"])
def test_claim_rejects_blank_text(text):
    with pytest.raises(ValueError, match="text"):
        Claim(CLAIM_ID, text)


@pytest.mark.parametrize("text", ["", " \n\t"])
def test_observation_rejects_blank_passage_text(text):
    with pytest.raises(ValueError, match="passage_text"):
        EvidenceObservation(
            passage_id=PASSAGE_ID,
            source_id=SOURCE_ID,
            source_sha256=None,
            location=None,
            passage_text=text,
            stance=EvidenceStance.SUPPORTS,
        )


def test_observation_rejects_invalid_stance():
    with pytest.raises(TypeError, match="stance"):
        EvidenceObservation(
            passage_id=PASSAGE_ID,
            source_id=SOURCE_ID,
            source_sha256=None,
            location=None,
            passage_text="Evidence text.",
            stance="supports",
        )


@pytest.mark.parametrize(
    ("outcome", "observations"),
    [
        (AssessmentOutcome.SUPPORTED, ()),
        (
            AssessmentOutcome.CONTRADICTED,
            (make_observation(EvidenceStance.IRRELEVANT),),
        ),
        (
            AssessmentOutcome.CONFLICTING,
            (make_observation(EvidenceStance.SUPPORTS),),
        ),
        (
            AssessmentOutcome.INSUFFICIENT_EVIDENCE,
            (make_observation(EvidenceStance.CONTRADICTS),),
        ),
    ],
)
def test_assessment_rejects_outcome_inconsistent_with_observations(
    outcome,
    observations,
):
    with pytest.raises(ValueError, match="evidence"):
        make_assessment(outcome, observations)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"assessment_id": "not-a-uuid"},
        {"claim_id": "not-a-uuid"},
        {"claim_text": ""},
        {"claim_text": " \t "},
        {"outcome": "supported"},
        {"review_state": "human_reviewed"},
    ],
)
def test_assessment_rejects_invalid_fields(kwargs):
    values = {
        "assessment_id": ASSESSMENT_ID,
        "claim_id": CLAIM_ID,
        "claim_text": "The treatment reduces symptoms.",
        "outcome": AssessmentOutcome.SUPPORTED,
        "evidence": (make_observation(EvidenceStance.SUPPORTS),),
        "review_state": ReviewState.HUMAN_REVIEWED,
    }
    values.update(kwargs)

    with pytest.raises((TypeError, ValueError)):
        ClaimAssessment(**values)


def test_assessment_rejects_non_tuple_or_malformed_evidence():
    with pytest.raises(TypeError, match="tuple"):
        make_assessment(AssessmentOutcome.INSUFFICIENT_EVIDENCE, [])
    with pytest.raises(TypeError, match="EvidenceObservation"):
        make_assessment(AssessmentOutcome.INSUFFICIENT_EVIDENCE, ("evidence",))


def test_records_and_evidence_collection_are_immutable():
    observation = make_observation(EvidenceStance.SUPPORTS)
    claim = Claim(CLAIM_ID, "The treatment reduces symptoms.")
    assessment = make_assessment(
        AssessmentOutcome.SUPPORTED,
        (observation,),
    )

    with pytest.raises(FrozenInstanceError):
        claim.text = "Changed."
    with pytest.raises(FrozenInstanceError):
        observation.stance = EvidenceStance.CONTRADICTS
    with pytest.raises(FrozenInstanceError):
        assessment.outcome = AssessmentOutcome.CONTRADICTED
    assert isinstance(assessment.evidence, tuple)


def test_retrieval_scores_and_ranks_are_not_assessment_fields():
    assessment_fields = {field.name for field in fields(ClaimAssessment)}
    observation_fields = {field.name for field in fields(EvidenceObservation)}

    assert "score" not in assessment_fields | observation_fields
    assert "rank" not in assessment_fields | observation_fields
    assert "stance" in observation_fields
