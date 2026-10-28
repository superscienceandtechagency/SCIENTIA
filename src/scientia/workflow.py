"""Deterministic orchestration for local evidence-grounded research workflows."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from scientia import retrieval as retrieval_module
from scientia.evidence import Passage, Source, validate_passage_source
from scientia.pdf_ingestion import PdfIngestionError, PdfIngestionResult, ingest_pdf
from scientia.retrieval import RetrievalHit, retrieve
from scientia.synthesis import ResearchQuestion, SynthesisResult, synthesize
from scientia.verification import ClaimAssessment, ReviewState

MAX_RESEARCH_PDF_COUNT = 8


@dataclass(frozen=True)
class PreparedResearch:
    """Question, ordered PDF ingestion records, and lexical retrieval hits."""

    question: ResearchQuestion
    ingestion_results: tuple[PdfIngestionResult, ...]
    retrieval_hits: tuple[RetrievalHit, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.question, ResearchQuestion):
            raise TypeError("question must be a ResearchQuestion")
        if not isinstance(self.ingestion_results, tuple):
            raise TypeError("ingestion_results must be a tuple")
        if any(
            not isinstance(item, PdfIngestionResult) for item in self.ingestion_results
        ):
            raise TypeError(
                "ingestion_results must contain only PdfIngestionResult records"
            )
        if not isinstance(self.retrieval_hits, tuple):
            raise TypeError("retrieval_hits must be a tuple")
        if any(not isinstance(item, RetrievalHit) for item in self.retrieval_hits):
            raise TypeError("retrieval_hits must contain only RetrievalHit records")
        _, ingested_passages = _ingested_provenance(self)
        for hit in self.retrieval_hits:
            passage = hit.passage
            if not isinstance(passage, Passage):
                raise TypeError("retrieval hit passage must be a Passage")
            ingested = ingested_passages.get((passage.source_id, passage.passage_id))
            if ingested is None or (
                passage.text != ingested.text
                or passage.location != ingested.location
            ):
                raise ValueError(
                    "retrieval hit passage must match an ingested passage"
                )
        expected_hits = retrieval_module.retrieve(
            self.question.text,
            tuple(ingested_passages.values()),
            limit=max(1, len(self.retrieval_hits)),
        )
        if self.retrieval_hits != expected_hits:
            raise ValueError(
                "retrieval hits must match the ranked results for the question"
            )


@dataclass(frozen=True)
class ResearchWorkflowResult:
    """Prepared evidence, submitted assessments, and their synthesis."""

    prepared: PreparedResearch
    assessments: tuple[ClaimAssessment, ...]
    synthesis: SynthesisResult

    def __post_init__(self) -> None:
        if not isinstance(self.prepared, PreparedResearch):
            raise TypeError("prepared must be a PreparedResearch")
        if not isinstance(self.assessments, tuple):
            raise TypeError("assessments must be a tuple")
        if any(not isinstance(item, ClaimAssessment) for item in self.assessments):
            raise TypeError("assessments must contain only ClaimAssessment records")
        if not isinstance(self.synthesis, SynthesisResult):
            raise TypeError("synthesis must be a SynthesisResult")
        if self.synthesis.question != self.prepared.question:
            raise ValueError("synthesis question must match prepared research question")
        expected_findings: list[ClaimAssessment] = []
        expected_unresolved: list[ClaimAssessment] = []
        for assessment in self.assessments:
            if (
                assessment.review_state is ReviewState.HUMAN_REVIEWED
                and assessment.outcome is not None
            ):
                expected_findings.append(assessment)
            else:
                expected_unresolved.append(assessment)
        actual_findings = tuple(
            finding.assessment for finding in self.synthesis.findings
        )
        if (
            actual_findings != tuple(expected_findings)
            or self.synthesis.unresolved_assessments != tuple(expected_unresolved)
        ):
            raise ValueError(
                "synthesis assessments must match submitted assessments in order"
            )
        sources, passages = _ingested_provenance(self.prepared)
        for assessment in self.assessments:
            _validate_assessment_provenance(assessment, sources, passages)


def _validate_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError("limit must be a positive integer")
    if limit <= 0:
        raise ValueError("limit must be a positive integer")


def prepare_research(
    question: ResearchQuestion,
    pdf_paths: Sequence[str | Path],
    limit: int = 10,
) -> PreparedResearch:
    """Ingest PDFs in order and retrieve passages using the question text.

    Ingestion errors propagate unchanged; the function returns no partial
    preparation. An empty hit tuple is a valid retrieval result and does not
    imply that evidence is absent or contradictory.
    """
    if not isinstance(question, ResearchQuestion):
        raise TypeError("question must be a ResearchQuestion")
    if isinstance(pdf_paths, (str, bytes)) or not isinstance(pdf_paths, Sequence):
        raise TypeError("pdf_paths must be a sequence of filesystem paths")
    if any(not isinstance(path, (str, Path)) for path in pdf_paths):
        raise TypeError("pdf_paths must contain only strings or Path objects")
    if len(pdf_paths) > MAX_RESEARCH_PDF_COUNT:
        raise PdfIngestionError(
            f"PDF count limit is {MAX_RESEARCH_PDF_COUNT}",
            stage="validate",
        )
    try:
        canonical_paths = tuple(Path(path).resolve() for path in pdf_paths)
    except (OSError, RuntimeError, ValueError) as exc:
        raise PdfIngestionError(
            "Could not validate PDF input paths",
            stage="validate",
        ) from exc
    if len(set(canonical_paths)) != len(canonical_paths):
        raise PdfIngestionError(
            "Duplicate PDF input paths are not allowed",
            stage="validate",
        )
    _validate_limit(limit)

    ingestion_results = tuple(ingest_pdf(path) for path in pdf_paths)
    content_hashes = [item.source.content_sha256 for item in ingestion_results]
    if len(set(content_hashes)) != len(content_hashes):
        raise PdfIngestionError(
            "Duplicate PDF content is not allowed",
            stage="validate",
        )
    passages = tuple(
        passage
        for result in ingestion_results
        for passage in result.passages
    )
    retrieval_hits = retrieve(question.text, passages, limit=limit)
    return PreparedResearch(
        question=question,
        ingestion_results=ingestion_results,
        retrieval_hits=retrieval_hits,
    )


def _ingested_provenance(
    prepared: PreparedResearch,
) -> tuple[dict[UUID, Source], dict[tuple[UUID, UUID], Passage]]:
    sources: dict[UUID, Source] = {}
    passages: dict[tuple[UUID, UUID], Passage] = {}
    for result in prepared.ingestion_results:
        source = result.source
        if not isinstance(source, Source):
            raise TypeError("ingestion result source must be a Source")
        existing_source = sources.get(source.source_id)
        if existing_source is not None and existing_source != source:
            raise ValueError("prepared research has ambiguous source provenance")
        sources[source.source_id] = source
        for passage in result.passages:
            if not isinstance(passage, Passage):
                raise TypeError("ingestion results must contain Passage records")
            validate_passage_source(source, passage)
            key = (passage.source_id, passage.passage_id)
            existing_passage = passages.get(key)
            if existing_passage is not None and existing_passage != passage:
                raise ValueError("prepared research has ambiguous passage provenance")
            passages[key] = passage
    return sources, passages


def _validate_assessment_provenance(
    assessment: ClaimAssessment,
    sources: dict[UUID, Source],
    passages: dict[tuple[UUID, UUID], Passage],
) -> None:
    for observation in assessment.evidence:
        source = sources.get(observation.source_id)
        if source is None:
            raise ValueError(
                f"assessment references unknown source {observation.source_id}"
            )
        passage = passages.get((observation.source_id, observation.passage_id))
        if passage is None:
            raise ValueError(
                f"assessment references unknown passage {observation.passage_id}"
            )
        if observation.source_sha256 != source.content_sha256:
            raise ValueError(
                f"assessment source hash does not match source "
                f"{observation.source_id}"
            )
        if observation.location != passage.location:
            raise ValueError(
                f"assessment location does not match passage "
                f"{observation.passage_id}"
            )
        if observation.passage_text != passage.text:
            raise ValueError(
                f"assessment text does not match passage {observation.passage_id}"
            )


def finalize_research(
    prepared: PreparedResearch,
    assessments: Sequence[ClaimAssessment],
) -> ResearchWorkflowResult:
    """Validate submitted provenance and synthesize without changing judgments."""
    if not isinstance(prepared, PreparedResearch):
        raise TypeError("prepared must be a PreparedResearch")
    if isinstance(assessments, (str, bytes)) or not isinstance(
        assessments, Sequence
    ):
        raise TypeError("assessments must be a sequence of ClaimAssessment records")
    if any(not isinstance(item, ClaimAssessment) for item in assessments):
        raise TypeError("assessments must contain only ClaimAssessment records")

    submitted = tuple(assessments)
    result = synthesize(prepared.question, submitted)
    return ResearchWorkflowResult(
        prepared=prepared,
        assessments=submitted,
        synthesis=result,
    )
