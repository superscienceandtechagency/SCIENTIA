"""Human-reviewed claim/evidence records; validation does not establish truth."""

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from scientia.evidence import (
    Location,
    Passage,
    Source,
    validate_passage_source,
)


class EvidenceStance(str, Enum):
    """A reviewer's interpretation of one passage relative to a claim."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    IRRELEVANT = "irrelevant"
    UNCLEAR = "unclear"


class AssessmentOutcome(str, Enum):
    """Human-reviewed summary label for the cited evidence set."""

    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING = "conflicting"


class ReviewState(str, Enum):
    """Workflow state of a claim assessment."""

    DRAFT = "draft"
    NEEDS_CLARIFICATION = "needs_clarification"
    HUMAN_REVIEWED = "human_reviewed"


def _require_non_blank(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _require_optional_non_blank(value: str | None, field_name: str) -> None:
    if value is not None:
        _require_non_blank(value, field_name)


def _require_uuid(value: UUID, field_name: str) -> None:
    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be a UUID")


@dataclass(frozen=True)
class Claim:
    """One claim, ideally atomic; ambiguous or compound text is not decomposed."""

    claim_id: UUID
    text: str

    def __post_init__(self) -> None:
        _require_uuid(self.claim_id, "claim_id")
        _require_non_blank(self.text, "text")


@dataclass(frozen=True)
class EvidenceObservation:
    """A stance and exact provenance snapshot for one human-reviewed passage.

    Record validation checks field and source-link consistency only. It does
    not determine semantic entailment or scientific truth.
    """

    passage_id: UUID
    source_id: UUID
    source_sha256: str | None
    location: Location | None
    passage_text: str
    stance: EvidenceStance
    reviewer_note: str | None = None

    def __post_init__(self) -> None:
        _require_uuid(self.passage_id, "passage_id")
        _require_uuid(self.source_id, "source_id")
        if self.source_sha256 is not None:
            if not isinstance(self.source_sha256, str):
                raise TypeError("source_sha256 must be a string or None")
            if (
                len(self.source_sha256) != 64
                or any(char not in "0123456789abcdef" for char in self.source_sha256)
            ):
                raise ValueError(
                    "source_sha256 must be 64 lowercase hexadecimal characters"
                )
        if self.location is not None and not isinstance(self.location, Location):
            raise TypeError("location must be a Location or None")
        _require_non_blank(self.passage_text, "passage_text")
        if not isinstance(self.stance, EvidenceStance):
            raise TypeError("stance must be an EvidenceStance")
        _require_optional_non_blank(self.reviewer_note, "reviewer_note")

    @classmethod
    def from_source_passage(
        cls,
        source: Source,
        passage: Passage,
        stance: EvidenceStance,
        *,
        reviewer_note: str | None = None,
    ) -> "EvidenceObservation":
        """Snapshot a passage after checking that it references the source."""
        validate_passage_source(source, passage)
        return cls(
            passage_id=passage.passage_id,
            source_id=source.source_id,
            source_sha256=source.content_sha256,
            location=passage.location,
            passage_text=passage.text,
            stance=stance,
            reviewer_note=reviewer_note,
        )


@dataclass(frozen=True)
class ClaimAssessment:
    """Human assessment record, not an automated scientific truth verdict.

    Outcome validation checks consistency with recorded stances; it cannot
    verify that a stance correctly interprets the passage or claim.
    """

    assessment_id: UUID
    claim_id: UUID
    claim_text: str
    outcome: AssessmentOutcome | None
    evidence: tuple[EvidenceObservation, ...]
    review_state: ReviewState
    reviewer_label: str | None = None
    rationale: str | None = None

    def __post_init__(self) -> None:
        _require_uuid(self.assessment_id, "assessment_id")
        _require_uuid(self.claim_id, "claim_id")
        _require_non_blank(self.claim_text, "claim_text")
        if self.outcome is not None and not isinstance(
            self.outcome, AssessmentOutcome
        ):
            raise TypeError("outcome must be an AssessmentOutcome or None")
        if not isinstance(self.evidence, tuple):
            raise TypeError("evidence must be a tuple")
        if any(not isinstance(item, EvidenceObservation) for item in self.evidence):
            raise TypeError("evidence must contain only EvidenceObservation records")
        if not isinstance(self.review_state, ReviewState):
            raise TypeError("review_state must be a ReviewState")
        evidence_ids = tuple(
            (observation.source_id, observation.passage_id)
            for observation in self.evidence
        )
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidence must not contain a duplicate evidence passage")
        _require_optional_non_blank(self.reviewer_label, "reviewer_label")
        _require_optional_non_blank(self.rationale, "rationale")
        self._validate_outcome_consistency()

    def _validate_outcome_consistency(self) -> None:
        stances = {observation.stance for observation in self.evidence}
        has_support = EvidenceStance.SUPPORTS in stances
        has_contradiction = EvidenceStance.CONTRADICTS in stances
        if has_support and has_contradiction:
            if self.outcome is not AssessmentOutcome.CONFLICTING:
                raise ValueError(
                    "mixed supporting and contradicting evidence requires a "
                    "conflicting outcome"
                )
        if self.outcome is AssessmentOutcome.SUPPORTED:
            if EvidenceStance.SUPPORTS not in stances:
                raise ValueError("supported outcome requires supporting evidence")
        elif self.outcome is AssessmentOutcome.CONTRADICTED:
            if EvidenceStance.CONTRADICTS not in stances:
                raise ValueError("contradicted outcome requires contradicting evidence")
        elif self.outcome is AssessmentOutcome.CONFLICTING:
            if not {
                EvidenceStance.SUPPORTS,
                EvidenceStance.CONTRADICTS,
            }.issubset(stances):
                raise ValueError(
                    "conflicting outcome requires supporting and contradicting "
                    "evidence"
                )
        elif self.outcome is AssessmentOutcome.INSUFFICIENT_EVIDENCE:
            if stances & {EvidenceStance.SUPPORTS, EvidenceStance.CONTRADICTS}:
                raise ValueError(
                    "insufficient_evidence requires only irrelevant or unclear "
                    "evidence"
                )
