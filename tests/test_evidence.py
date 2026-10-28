from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from scientia.evidence import Location, Passage, Source, validate_passage_source

SOURCE_ID = UUID("d86ccf62-40d9-4e9e-9fa8-ddcef1e96965")
PASSAGE_ID = UUID("bc985857-a671-4369-a5da-8776f2438a1a")
OTHER_SOURCE_ID = UUID("ecab803c-70d0-4b90-9826-98a977d5b5c8")


def test_source_preserves_supplied_identity_and_optional_metadata():
    source = Source(
        source_id=SOURCE_ID,
        title="  Example study  ",
        locator="doi:10.xxxx/example",
        content_sha256="a" * 64,
    )

    assert source.source_id == SOURCE_ID
    assert source.title == "  Example study  "
    assert source.locator == "doi:10.xxxx/example"
    assert source.content_sha256 == "a" * 64
    with pytest.raises(FrozenInstanceError):
        source.title = "Changed"


def test_source_metadata_can_be_omitted():
    assert Source(source_id=SOURCE_ID).title is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"source_id": "not-a-uuid"},
        {"source_id": None},
        {"source_id": SOURCE_ID, "title": ""},
        {"source_id": SOURCE_ID, "title": " \t"},
        {"source_id": SOURCE_ID, "locator": ""},
        {"source_id": SOURCE_ID, "content_sha256": "A" * 64},
        {"source_id": SOURCE_ID, "content_sha256": "g" * 64},
        {"source_id": SOURCE_ID, "content_sha256": "a" * 63},
    ],
)
def test_source_rejects_invalid_fields(kwargs):
    with pytest.raises((TypeError, ValueError)):
        Source(**kwargs)


def test_location_accepts_page_only_section_only_or_both():
    assert Location(page_start=2, page_end=3).page_end == 3
    assert Location(section_path=("Results", "Primary outcome")).section_path == (
        "Results",
        "Primary outcome",
    )
    assert Location(
        page_start=4,
        page_end=4,
        section_path=("Methods",),
    ).page_start == 4


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"page_start": 0, "page_end": 1},
        {"page_start": 1},
        {"page_end": 1},
        {"page_start": 3, "page_end": 2},
        {"page_start": True, "page_end": 1},
        {"section_path": ()},
        {"section_path": ("Results", "")},
        {"section_path": ("Results", " ")},
        {"section_path": "Results"},
    ],
)
def test_location_rejects_invalid_fields(kwargs):
    with pytest.raises((TypeError, ValueError)):
        Location(**kwargs)


def test_passage_preserves_ids_text_and_optional_unknown_location():
    text = "  The reported estimate was 1.2.  "
    passage = Passage(
        passage_id=PASSAGE_ID,
        source_id=SOURCE_ID,
        text=text,
        location=None,
    )

    assert passage.passage_id == PASSAGE_ID
    assert passage.source_id == SOURCE_ID
    assert passage.text == text
    assert passage.location is None
    with pytest.raises(FrozenInstanceError):
        passage.text = "Changed"


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"passage_id": PASSAGE_ID, "text": "Body"},
        {"source_id": SOURCE_ID, "text": "Body"},
        {"passage_id": PASSAGE_ID, "source_id": SOURCE_ID},
        {"passage_id": "not-a-uuid", "source_id": SOURCE_ID, "text": "Body"},
        {"passage_id": PASSAGE_ID, "source_id": "not-a-uuid", "text": "Body"},
        {"passage_id": PASSAGE_ID, "source_id": SOURCE_ID, "text": ""},
        {"passage_id": PASSAGE_ID, "source_id": SOURCE_ID, "text": " \n\t"},
    ],
)
def test_passage_rejects_invalid_fields(kwargs):
    with pytest.raises((TypeError, ValueError)):
        Passage(**kwargs)


def test_passage_source_link_accepts_matching_source():
    source = Source(source_id=SOURCE_ID)
    passage = Passage(passage_id=PASSAGE_ID, source_id=SOURCE_ID, text="Evidence")

    validate_passage_source(source, passage)


def test_passage_source_link_rejects_mismatched_source():
    source = Source(source_id=SOURCE_ID)
    passage = Passage(
        passage_id=PASSAGE_ID,
        source_id=OTHER_SOURCE_ID,
        text="Evidence",
    )

    with pytest.raises(ValueError, match="source"):
        validate_passage_source(source, passage)
