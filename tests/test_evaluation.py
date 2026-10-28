import json
from uuid import UUID

import pytest

from scientia.evaluation import (
    benchmark_report,
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from scientia.retrieval import retrieve
from scientia.retrieval_benchmark import (
    BENCHMARK_ID,
    SYNTHETIC_JUDGMENTS,
    SYNTHETIC_PASSAGES,
)

ID_A = UUID("00000000-0000-0000-0000-000000000001")
ID_B = UUID("00000000-0000-0000-0000-000000000002")
ID_C = UUID("00000000-0000-0000-0000-000000000003")
ID_D = UUID("00000000-0000-0000-0000-000000000004")


def test_precision_at_k_uses_k_as_denominator():
    assert precision_at_k((ID_A, ID_B, ID_C), {ID_B, ID_C, ID_D}, 2) == 0.5
    assert precision_at_k((ID_A, ID_B, ID_C), {ID_C, ID_D}, 2) == 0.0


def test_recall_at_k_counts_judged_relevant_ids_in_prefix():
    assert recall_at_k((ID_A, ID_B, ID_C), {ID_B, ID_C, ID_D}, 2) == pytest.approx(
        1 / 3
    )


@pytest.mark.parametrize(
    ("ranked_ids", "expected"),
    [
        ((ID_B, ID_A), 1.0),
        ((ID_A, ID_B), 0.5),
        ((ID_A, ID_C, ID_B), 1 / 3),
        ((), 0.0),
    ],
)
def test_reciprocal_rank_uses_first_relevant_rank(ranked_ids, expected):
    assert reciprocal_rank(ranked_ids, {ID_B}) == expected


def test_empty_results_with_nonempty_relevance_are_zero():
    assert precision_at_k((), {ID_A}, 3) == 0.0
    assert recall_at_k((), {ID_A}, 3) == 0.0
    assert reciprocal_rank((), {ID_A}) == 0.0


def test_empty_judgments_are_undefined_for_recall_and_reciprocal_rank():
    assert recall_at_k((ID_A,), set(), 3) is None
    assert reciprocal_rank((ID_A,), set()) is None


def test_mrr_excludes_queries_with_empty_judgments_and_reports_count():
    summary = mean_reciprocal_rank(
        ((ID_A,), (ID_B,), ()),
        ({ID_A}, {ID_C}, set()),
    )

    assert summary.value == 0.5
    assert summary.included_queries == 2
    assert summary.excluded_queries == 1


def test_mrr_is_undefined_when_all_judgments_are_empty():
    summary = mean_reciprocal_rank(((ID_A,), ()), (set(), set()))

    assert summary.value is None
    assert summary.included_queries == 0
    assert summary.excluded_queries == 2


@pytest.mark.parametrize("k", [0, -1, True, False, 1.5, "2", None])
def test_metrics_reject_invalid_k(k):
    with pytest.raises((TypeError, ValueError), match="k"):
        precision_at_k((), (), k)
    with pytest.raises((TypeError, ValueError), match="k"):
        recall_at_k((), (), k)


@pytest.mark.parametrize(
    ("ranked_ids", "relevant_ids"),
    [
        (("not-a-uuid",), {ID_A}),
        ((ID_A, ID_A), {ID_A}),
        ((ID_A,), ["not-a-uuid"]),
        ((ID_A,), [ID_A, ID_A]),
    ],
)
def test_metrics_reject_malformed_or_duplicate_ids(ranked_ids, relevant_ids):
    with pytest.raises((TypeError, ValueError), match="ID|UUID|duplicate"):
        precision_at_k(ranked_ids, relevant_ids, 1)


def test_mrr_rejects_mismatched_query_counts_and_duplicate_ids():
    with pytest.raises(ValueError, match="same number"):
        mean_reciprocal_rank(((ID_A,),), ())
    with pytest.raises(ValueError, match="duplicate"):
        mean_reciprocal_rank(((ID_A, ID_A),), ({ID_A},))


def test_synthetic_judgments_are_fixed_independently_of_retrieval():
    assert BENCHMARK_ID == "synthetic-lexical-v2"
    assert tuple(case.query_id for case in SYNTHETIC_JUDGMENTS) == (
        "fever-trial",
        "compound-adverse-events",
        "saline-irrigation",
        "astronomy-unknown",
        "exact-assay-match",
        "partial-saline-match",
        "cellular-energy-rank-error",
        "missing-lexical-terms",
    )
    assert SYNTHETIC_JUDGMENTS[0].relevant_passage_ids == {
        UUID("20000000-0000-0000-0000-000000000001")
    }
    assert SYNTHETIC_JUDGMENTS[1].relevant_passage_ids == {
        UUID("20000000-0000-0000-0000-000000000002"),
        UUID("20000000-0000-0000-0000-000000000003"),
    }
    assert SYNTHETIC_JUDGMENTS[3].relevant_passage_ids == frozenset()
    assert all(case.rationale.strip() for case in SYNTHETIC_JUDGMENTS)


def test_benchmark_report_identifies_lexical_failure_modes():
    report = benchmark_report()
    cases = {case["query_id"]: case for case in report["queries"]}

    exact = cases["exact-assay-match"]
    assert exact["relevant_rank_positions"] == [1]
    assert exact["missed_relevant_ids"] == []
    assert exact["irrelevant_retrieved_ids"]

    partial = cases["partial-saline-match"]
    assert partial["recall_at_k"] == 1.0
    assert partial["irrelevant_retrieved_ids"]

    rank_error = cases["cellular-energy-rank-error"]
    assert rank_error["relevant_rank_positions"] == [2]
    assert rank_error["ranking_errors"] == [
        {
            "relevant_passage_id": "20000000-0000-0000-0000-000000000008",
            "irrelevant_passage_id": "20000000-0000-0000-0000-000000000009",
            "relevant_rank": 2,
            "irrelevant_rank": 1,
        }
    ]

    missing = cases["missing-lexical-terms"]
    assert missing["retrieved_ids"] == []
    assert missing["missed_relevant_ids"] == [
        "20000000-0000-0000-0000-000000000010"
    ]
    assert missing["recall_at_k"] == 0.0
    assert missing["reciprocal_rank"] == 0.0

    unknown = cases["astronomy-unknown"]
    assert unknown["analysis_status"] == "no_relevance_judgments"
    assert unknown["irrelevant_retrieved_ids"] is None
    assert unknown["ranking_errors"] is None


def test_benchmark_report_does_not_mutate_fixed_corpus_or_judgments():
    before_passages = tuple(
        (passage.passage_id, passage.source_id, passage.text)
        for passage in SYNTHETIC_PASSAGES
    )
    before_judgments = tuple(
        (case.query_id, case.query, case.relevant_passage_ids, case.rationale)
        for case in SYNTHETIC_JUDGMENTS
    )

    benchmark_report()

    assert tuple(
        (passage.passage_id, passage.source_id, passage.text)
        for passage in SYNTHETIC_PASSAGES
    ) == before_passages
    assert tuple(
        (case.query_id, case.query, case.relevant_passage_ids, case.rationale)
        for case in SYNTHETIC_JUDGMENTS
    ) == before_judgments


def test_synthetic_benchmark_has_expected_deterministic_baseline_at_k3():
    ranked = tuple(
        tuple(
            hit.passage.passage_id
            for hit in retrieve(case.query, SYNTHETIC_PASSAGES, limit=3)
        )
        for case in SYNTHETIC_JUDGMENTS
    )
    assert ranked == (
        (
            UUID("20000000-0000-0000-0000-000000000001"),
            UUID("20000000-0000-0000-0000-000000000003"),
            UUID("20000000-0000-0000-0000-000000000006"),
        ),
        (
            UUID("20000000-0000-0000-0000-000000000002"),
            UUID("20000000-0000-0000-0000-000000000003"),
            UUID("20000000-0000-0000-0000-000000000001"),
        ),
        (
            UUID("20000000-0000-0000-0000-000000000004"),
            UUID("20000000-0000-0000-0000-000000000006"),
        ),
        (
            UUID("20000000-0000-0000-0000-000000000006"),
            UUID("20000000-0000-0000-0000-000000000001"),
            UUID("20000000-0000-0000-0000-000000000003"),
        ),
        (
            UUID("20000000-0000-0000-0000-000000000007"),
            UUID("20000000-0000-0000-0000-000000000001"),
            UUID("20000000-0000-0000-0000-000000000003"),
        ),
        (
            UUID("20000000-0000-0000-0000-000000000004"),
            UUID("20000000-0000-0000-0000-000000000006"),
        ),
        (
            UUID("20000000-0000-0000-0000-000000000009"),
            UUID("20000000-0000-0000-0000-000000000008"),
        ),
        (),
    )

    per_query_precision = tuple(
        precision_at_k(results, case.relevant_passage_ids, 3)
        for results, case in zip(ranked, SYNTHETIC_JUDGMENTS, strict=True)
    )
    per_query_recall = tuple(
        recall_at_k(results, case.relevant_passage_ids, 3)
        for results, case in zip(ranked, SYNTHETIC_JUDGMENTS, strict=True)
    )
    per_query_rr = tuple(
        reciprocal_rank(results, case.relevant_passage_ids)
        for results, case in zip(ranked, SYNTHETIC_JUDGMENTS, strict=True)
    )
    assert per_query_precision == pytest.approx(
        (1 / 3, 2 / 3, 1 / 3, 0, 1 / 3, 1 / 3, 1 / 3, 0)
    )
    assert per_query_recall == (1.0, 1.0, 1.0, None, 1.0, 1.0, 1.0, 0.0)
    assert per_query_rr == (1.0, 1.0, 1.0, None, 1.0, 1.0, 0.5, 0.0)
    assert sum(per_query_precision) / len(per_query_precision) == pytest.approx(
        7 / 24
    )

    summary = mean_reciprocal_rank(
        ranked,
        tuple(case.relevant_passage_ids for case in SYNTHETIC_JUDGMENTS),
    )
    assert summary.value == pytest.approx(11 / 14)
    assert summary.included_queries == 7
    assert summary.excluded_queries == 1


def test_synthetic_benchmark_rankings_repeat_exactly():
    def run():
        return tuple(
            tuple(
                (hit.passage.passage_id, hit.score)
                for hit in retrieve(case.query, SYNTHETIC_PASSAGES, limit=3)
            )
            for case in SYNTHETIC_JUDGMENTS
        )

    assert run() == run()


def test_benchmark_report_contains_deterministic_per_query_and_aggregate_metrics():
    report = benchmark_report()

    assert report["benchmark"] == "synthetic-lexical-v2"
    assert report["k"] == 3
    assert [case["query_id"] for case in report["queries"]] == [
        "fever-trial",
        "compound-adverse-events",
        "saline-irrigation",
        "astronomy-unknown",
        "exact-assay-match",
        "partial-saline-match",
        "cellular-energy-rank-error",
        "missing-lexical-terms",
    ]
    assert report["queries"][-1]["query"] == "Which molecule fuels biological work?"
    assert report["mean_precision_at_k"] == pytest.approx(7 / 24)
    assert report["mean_recall_at_k"] == pytest.approx(6 / 7)
    assert report["mean_reciprocal_rank"] == pytest.approx(11 / 14)
    assert report["mrr_included_queries"] == 7
    assert report["mrr_excluded_queries"] == 1


def test_benchmark_report_is_json_serializable_and_repeatable():
    assert benchmark_report() == benchmark_report()
    assert json.loads(json.dumps(benchmark_report())) == benchmark_report()
