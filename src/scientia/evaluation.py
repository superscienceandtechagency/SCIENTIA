"""Deterministic ranking metrics for retrieval evaluation."""

import json
from dataclasses import dataclass
from typing import Iterable, Sequence
from uuid import UUID

from scientia.retrieval import retrieve
from scientia.retrieval_benchmark import (
    BENCHMARK_ID,
    SYNTHETIC_JUDGMENTS,
    SYNTHETIC_PASSAGES,
)

BENCHMARK_K = 3


@dataclass(frozen=True)
class MeanReciprocalRank:
    """MRR and counts of queries included in or excluded from the mean."""

    value: float | None
    included_queries: int
    excluded_queries: int


def _validate_k(k: int) -> None:
    if isinstance(k, bool) or not isinstance(k, int):
        raise TypeError("k must be a positive integer")
    if k <= 0:
        raise ValueError("k must be a positive integer")


def _validated_ids(ids: Iterable[UUID], name: str) -> tuple[UUID, ...]:
    try:
        values = tuple(ids)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of UUID IDs") from exc
    if any(not isinstance(value, UUID) for value in values):
        raise TypeError(f"{name} must contain only UUID IDs")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicate IDs")
    return values


def precision_at_k(
    retrieved_ids: Iterable[UUID],
    relevant_ids: Iterable[UUID],
    k: int,
) -> float:
    """Return relevant retrieved IDs in the first k ranks divided by k."""
    _validate_k(k)
    ranked = _validated_ids(retrieved_ids, "retrieved IDs")
    relevant = set(_validated_ids(relevant_ids, "relevant IDs"))
    return sum(passage_id in relevant for passage_id in ranked[:k]) / k


def recall_at_k(
    retrieved_ids: Iterable[UUID],
    relevant_ids: Iterable[UUID],
    k: int,
) -> float | None:
    """Return Recall@k, or None when no relevant IDs were judged."""
    _validate_k(k)
    ranked = _validated_ids(retrieved_ids, "retrieved IDs")
    relevant = set(_validated_ids(relevant_ids, "relevant IDs"))
    if not relevant:
        return None
    return sum(passage_id in relevant for passage_id in ranked[:k]) / len(relevant)


def reciprocal_rank(
    retrieved_ids: Iterable[UUID],
    relevant_ids: Iterable[UUID],
) -> float | None:
    """Return the first relevant result's reciprocal rank, or None if undefined."""
    ranked = _validated_ids(retrieved_ids, "retrieved IDs")
    relevant = set(_validated_ids(relevant_ids, "relevant IDs"))
    if not relevant:
        return None
    for rank, passage_id in enumerate(ranked, start=1):
        if passage_id in relevant:
            return 1 / rank
    return 0.0


def mean_reciprocal_rank(
    rankings: Sequence[Iterable[UUID]],
    relevance_judgments: Sequence[Iterable[UUID]],
) -> MeanReciprocalRank:
    """Average defined reciprocal ranks and report excluded unjudged queries."""
    if len(rankings) != len(relevance_judgments):
        raise ValueError("rankings and relevance judgments must have the same number")

    reciprocal_ranks = tuple(
        reciprocal_rank(ranked_ids, relevant_ids)
        for ranked_ids, relevant_ids in zip(
            rankings, relevance_judgments, strict=True
        )
    )
    defined = tuple(value for value in reciprocal_ranks if value is not None)
    return MeanReciprocalRank(
        value=sum(defined) / len(defined) if defined else None,
        included_queries=len(defined),
        excluded_queries=len(reciprocal_ranks) - len(defined),
    )


def benchmark_report() -> dict[str, object]:
    """Return a deterministic JSON-safe report for the fixed synthetic corpus."""
    ranked_hits = tuple(
        retrieve(judgment.query, SYNTHETIC_PASSAGES, limit=BENCHMARK_K)
        for judgment in SYNTHETIC_JUDGMENTS
    )
    rankings = tuple(
        tuple(hit.passage.passage_id for hit in hits) for hits in ranked_hits
    )
    relevance = tuple(
        judgment.relevant_passage_ids for judgment in SYNTHETIC_JUDGMENTS
    )
    per_query_precision = tuple(
        precision_at_k(ranked, relevant, BENCHMARK_K)
        for ranked, relevant in zip(rankings, relevance, strict=True)
    )
    per_query_recall = tuple(
        recall_at_k(ranked, relevant, BENCHMARK_K)
        for ranked, relevant in zip(rankings, relevance, strict=True)
    )
    per_query_rr = tuple(
        reciprocal_rank(ranked, relevant)
        for ranked, relevant in zip(rankings, relevance, strict=True)
    )
    defined_recall = tuple(value for value in per_query_recall if value is not None)
    mrr = mean_reciprocal_rank(rankings, relevance)

    query_reports: list[dict[str, object]] = []
    for judgment, hits, ranked, precision, recall, rr in zip(
        SYNTHETIC_JUDGMENTS,
        ranked_hits,
        rankings,
        per_query_precision,
        per_query_recall,
        per_query_rr,
        strict=True,
    ):
        ranked_set = set(ranked)
        relevant_positions = {
            passage_id: rank
            for rank, passage_id in enumerate(ranked, start=1)
            if passage_id in judgment.relevant_passage_ids
        }
        irrelevant_positions = {
            passage_id: rank
            for rank, passage_id in enumerate(ranked, start=1)
            if passage_id not in judgment.relevant_passage_ids
        }
        if judgment.relevant_passage_ids:
            missed = sorted(
                judgment.relevant_passage_ids - ranked_set, key=str
            )
            irrelevant = tuple(irrelevant_positions)
            ranking_errors = [
                {
                    "relevant_passage_id": str(relevant_id),
                    "irrelevant_passage_id": str(irrelevant_id),
                    "relevant_rank": relevant_rank,
                    "irrelevant_rank": irrelevant_rank,
                }
                for relevant_id, relevant_rank in relevant_positions.items()
                for irrelevant_id, irrelevant_rank in irrelevant_positions.items()
                if irrelevant_rank < relevant_rank
            ]
            failure_analysis: dict[str, object] = {
                "analysis_status": "judged",
                "missed_relevant_ids": [str(passage_id) for passage_id in missed],
                "irrelevant_retrieved_ids": [
                    str(passage_id) for passage_id in irrelevant
                ],
                "relevant_rank_positions": list(relevant_positions.values()),
                "ranking_errors": ranking_errors,
            }
        else:
            failure_analysis = {
                "analysis_status": "no_relevance_judgments",
                "missed_relevant_ids": None,
                "irrelevant_retrieved_ids": None,
                "relevant_rank_positions": None,
                "ranking_errors": None,
            }

        query_reports.append(
            {
                "query_id": judgment.query_id,
                "query": judgment.query,
                "relevance_rationale": judgment.rationale,
                "retrieved_ids": [str(passage_id) for passage_id in ranked],
                "ranked_results": [
                    {
                        "passage_id": str(hit.passage.passage_id),
                        "score": hit.score,
                    }
                    for hit in hits
                ],
                "precision_at_k": precision,
                "recall_at_k": recall,
                "reciprocal_rank": rr,
                **failure_analysis,
            }
        )

    return {
        "benchmark": BENCHMARK_ID,
        "k": BENCHMARK_K,
        "queries": query_reports,
        "mean_precision_at_k": sum(per_query_precision) / len(per_query_precision),
        "mean_recall_at_k": (
            sum(defined_recall) / len(defined_recall) if defined_recall else None
        ),
        "mean_reciprocal_rank": mrr.value,
        "mrr_included_queries": mrr.included_queries,
        "mrr_excluded_queries": mrr.excluded_queries,
    }


def main() -> int:
    """Print the fixed synthetic retrieval benchmark as JSON."""
    print(json.dumps(benchmark_report(), ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
