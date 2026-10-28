from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from scientia.evidence import Location, Passage
from scientia.retrieval import RetrievalHit, retrieve

SOURCE_A = UUID("00000000-0000-0000-0000-000000000001")
SOURCE_B = UUID("00000000-0000-0000-0000-000000000002")
PASSAGE_A = UUID("00000000-0000-0000-0000-000000000011")
PASSAGE_B = UUID("00000000-0000-0000-0000-000000000012")
PASSAGE_C = UUID("00000000-0000-0000-0000-000000000013")
PASSAGE_D = UUID("00000000-0000-0000-0000-000000000014")

PASSAGES = (
    Passage(
        passage_id=PASSAGE_A,
        source_id=SOURCE_B,
        text="Adverse events were monitored during the randomized trial.",
        location=Location(page_start=4, page_end=4),
    ),
    Passage(
        passage_id=PASSAGE_B,
        source_id=SOURCE_A,
        text="The study reports adverse events.",
        location=Location(section_path=("Results",)),
    ),
    Passage(
        passage_id=PASSAGE_C,
        source_id=SOURCE_A,
        text="Outcomes and adverse events were recorded.",
        location=None,
    ),
    Passage(
        passage_id=PASSAGE_D,
        source_id=SOURCE_B,
        text="Stars and galaxies were observed through a telescope.",
        location=Location(page_start=9, page_end=9),
    ),
)


def test_exact_keyword_match_returns_original_passage():
    results = retrieve("telescope", PASSAGES)

    assert len(results) == 1
    assert results[0] == RetrievalHit(passage=PASSAGES[3], score=1)
    assert results[0].passage is PASSAGES[3]


def test_matching_is_casefolded_and_unicode_aware():
    passage = Passage(
        passage_id=PASSAGE_A,
        source_id=SOURCE_A,
        text="Café measurements were reproducible.",
    )

    results = retrieve("CAFÉ", (passage,))

    assert results[0].passage is passage
    assert results[0].score == 1


def test_distinct_query_token_overlap_ranks_relevant_passages():
    results = retrieve("adverse adverse events trial", PASSAGES)

    assert [hit.passage.passage_id for hit in results] == [
        PASSAGE_A,
        PASSAGE_B,
        PASSAGE_C,
    ]
    assert [hit.score for hit in results] == [3, 2, 2]


def test_ties_use_source_then_passage_uuid_independent_of_input_order():
    first_order = retrieve("adverse events", PASSAGES)
    reverse_order = retrieve("adverse events", tuple(reversed(PASSAGES)))

    assert [hit.passage.passage_id for hit in first_order] == [
        PASSAGE_B,
        PASSAGE_C,
        PASSAGE_A,
    ]
    assert [hit.passage.passage_id for hit in reverse_order] == [
        PASSAGE_B,
        PASSAGE_C,
        PASSAGE_A,
    ]


def test_results_include_matches_across_multiple_sources():
    results = retrieve("adverse", PASSAGES)

    assert {hit.passage.source_id for hit in results} == {SOURCE_A, SOURCE_B}


@pytest.mark.parametrize("query", ["", " \t\n"])
def test_blank_query_is_rejected(query):
    with pytest.raises(ValueError, match="query"):
        retrieve(query, PASSAGES)


def test_non_string_query_is_rejected():
    with pytest.raises(TypeError, match="query"):
        retrieve(None, PASSAGES)


def test_empty_collection_and_no_match_return_empty_tuple():
    assert retrieve("adverse", ()) == ()
    assert retrieve("quasar", PASSAGES) == ()


def test_limit_caps_results_and_accepts_only_positive_non_boolean_integers():
    assert len(retrieve("adverse events", PASSAGES, limit=1)) == 1

    for limit in (0, -1, 1.5, "2", True, False):
        with pytest.raises((TypeError, ValueError), match="limit"):
            retrieve("adverse", PASSAGES, limit=limit)


@pytest.mark.parametrize("passages", [(None,), ("not a passage",)])
def test_invalid_passage_entries_are_rejected(passages):
    with pytest.raises(TypeError, match="Passage"):
        retrieve("adverse", passages)


def test_hits_preserve_passage_provenance_and_text_exactly():
    original = PASSAGES[0]

    hit = retrieve("randomized trial", (original,))[0]

    assert hit.passage is original
    assert hit.passage.passage_id == PASSAGE_A
    assert hit.passage.source_id == SOURCE_B
    assert hit.passage.location == Location(page_start=4, page_end=4)
    assert hit.passage.text == (
        "Adverse events were monitored during the randomized trial."
    )


def test_retrieval_hit_is_immutable():
    hit = retrieve("telescope", PASSAGES)[0]

    with pytest.raises(FrozenInstanceError):
        hit.score = 0


def test_repeated_retrieval_returns_identical_ordered_hits():
    first = retrieve("adverse events trial", PASSAGES)
    second = retrieve("adverse events trial", PASSAGES)

    assert first == second
    assert [
        (hit.passage.passage_id, hit.score) for hit in first
    ] == [
        (hit.passage.passage_id, hit.score) for hit in second
    ]


def test_duplicate_passage_identity_is_rejected():
    passage = PASSAGES[0]

    with pytest.raises(ValueError, match="duplicate passage identity"):
        retrieve("randomized trial", (passage, passage))
