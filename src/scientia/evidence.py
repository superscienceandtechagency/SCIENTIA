"""Domain records for source documents and their evidence passages."""

from dataclasses import dataclass
from uuid import UUID


def _require_non_blank(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True)
class Source:
    """Identity and optional descriptive metadata for a source document."""

    source_id: UUID
    title: str | None = None
    locator: str | None = None
    content_sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, UUID):
            raise TypeError("source_id must be a UUID")
        for field_name, value in (("title", self.title), ("locator", self.locator)):
            if value is not None:
                _require_non_blank(value, field_name)
        if self.content_sha256 is not None:
            if not isinstance(self.content_sha256, str):
                raise TypeError("content_sha256 must be a string")
            if (
                len(self.content_sha256) != 64
                or any(char not in "0123456789abcdef" for char in self.content_sha256)
            ):
                raise ValueError(
                    "content_sha256 must be 64 lowercase hexadecimal characters"
                )


@dataclass(frozen=True)
class Location:
    """Optional page range and/or hierarchical section location."""

    page_start: int | None = None
    page_end: int | None = None
    section_path: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if (self.page_start is None) != (self.page_end is None):
            raise ValueError("page_start and page_end must be provided together")
        if self.page_start is not None:
            if (
                isinstance(self.page_start, bool)
                or not isinstance(self.page_start, int)
                or isinstance(self.page_end, bool)
                or not isinstance(self.page_end, int)
            ):
                raise TypeError("page numbers must be integers")
            if self.page_start < 1 or self.page_end < 1:
                raise ValueError("page numbers must be positive")
            if self.page_end < self.page_start:
                raise ValueError("page_end must be greater than or equal to page_start")
        if self.section_path is not None:
            if not isinstance(self.section_path, tuple):
                raise TypeError("section_path must be a tuple of headings")
            if not self.section_path:
                raise ValueError("section_path must contain at least one heading")
            for heading in self.section_path:
                _require_non_blank(heading, "section heading")
        if self.page_start is None and self.section_path is None:
            raise ValueError("location must include pages or a section path")


@dataclass(frozen=True)
class Passage:
    """An exact text passage and its source and optional location references."""

    passage_id: UUID
    source_id: UUID
    text: str
    location: Location | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.passage_id, UUID):
            raise TypeError("passage_id must be a UUID")
        if not isinstance(self.source_id, UUID):
            raise TypeError("source_id must be a UUID")
        _require_non_blank(self.text, "text")
        if self.location is not None and not isinstance(self.location, Location):
            raise TypeError("location must be a Location or None")


def validate_passage_source(source: Source, passage: Passage) -> None:
    """Raise ValueError if a passage does not reference the supplied source."""
    if not isinstance(source, Source):
        raise TypeError("source must be a Source")
    if not isinstance(passage, Passage):
        raise TypeError("passage must be a Passage")
    if passage.source_id != source.source_id:
        raise ValueError("passage source_id does not match source source_id")
