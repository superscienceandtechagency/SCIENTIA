"""Deterministic organization of human-reviewed claim assessments."""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from scientia.verification import (
    AssessmentOutcome,
    ClaimAssessment,
    ReviewState,
)


@dataclass(frozen=True)
class ResearchQuestion:
    """A research question used to organize caller-selected assessments."""

    question_id: UUID
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.question_id, UUID):
            raise TypeError("question_id must be a UUID")
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if not self.text.strip():
            raise ValueError("text must not be blank")


@dataclass(frozen=True)
class SynthesisFinding:
    """A human-reviewed claim assessment with a recorded outcome."""

    assessment: ClaimAssessment

    def __post_init__(self) -> None:
        if not isinstance(self.assessment, ClaimAssessment):
            raise TypeError("assessment must be a ClaimAssessment")
        if self.assessment.review_state is not ReviewState.HUMAN_REVIEWED:
            raise ValueError("finding assessment must be HUMAN_REVIEWED")
        if not isinstance(self.assessment.outcome, AssessmentOutcome):
            raise ValueError("finding assessment must have a non-None outcome")


@dataclass(frozen=True)
class SynthesisResult:
    """A question and ordered tuples of reviewed findings and unresolved records.

    This record organizes supplied human assessments; it does not establish
    scientific truth, infer question relevance, or generate conclusions.
    """

    question: ResearchQuestion
    findings: tuple[SynthesisFinding, ...]
    unresolved_assessments: tuple[ClaimAssessment, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.question, ResearchQuestion):
            raise TypeError("question must be a ResearchQuestion")
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple")
        if any(not isinstance(item, SynthesisFinding) for item in self.findings):
            raise TypeError("findings must contain only SynthesisFinding records")
        if not isinstance(self.unresolved_assessments, tuple):
            raise TypeError("unresolved_assessments must be a tuple")
        if any(
            not isinstance(item, ClaimAssessment)
            for item in self.unresolved_assessments
        ):
            raise TypeError(
                "unresolved_assessments must contain only ClaimAssessment records"
            )
        if any(
            item.review_state is ReviewState.HUMAN_REVIEWED
            and item.outcome is not None
            for item in self.unresolved_assessments
        ):
            raise ValueError(
                "unresolved_assessments cannot contain completed assessments"
            )
        assessments = tuple(
            finding.assessment for finding in self.findings
        ) + self.unresolved_assessments
        assessment_ids = tuple(item.assessment_id for item in assessments)
        if len(set(assessment_ids)) != len(assessment_ids):
            raise ValueError("synthesis must not contain a duplicate assessment_id")
        claim_text_by_id: dict[UUID, str] = {}
        for assessment in assessments:
            existing_text = claim_text_by_id.get(assessment.claim_id)
            if existing_text is not None and existing_text != assessment.claim_text:
                raise ValueError(
                    "assessments with the same claim_id must have the same claim_text"
                )
            claim_text_by_id[assessment.claim_id] = assessment.claim_text


def synthesize(
    question: ResearchQuestion,
    assessments: Sequence[ClaimAssessment],
) -> SynthesisResult:
    """Separate completed human assessments from unresolved assessments.

    Input ordering is retained within both output tuples. The operation does
    not infer relevance from the question or use retrieval scores or ranks.
    """
    if not isinstance(question, ResearchQuestion):
        raise TypeError("question must be a ResearchQuestion")
    if isinstance(assessments, (str, bytes)) or not isinstance(
        assessments, Sequence
    ):
        raise TypeError("assessments must be a sequence of ClaimAssessment records")

    findings: list[SynthesisFinding] = []
    unresolved: list[ClaimAssessment] = []
    for assessment in assessments:
        if not isinstance(assessment, ClaimAssessment):
            raise TypeError("assessments must contain only ClaimAssessment records")
        if (
            assessment.review_state is ReviewState.HUMAN_REVIEWED
            and assessment.outcome is not None
        ):
            findings.append(SynthesisFinding(assessment))
        else:
            unresolved.append(assessment)

    return SynthesisResult(
        question=question,
        findings=tuple(findings),
        unresolved_assessments=tuple(unresolved),
    )
