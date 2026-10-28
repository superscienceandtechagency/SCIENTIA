"""Deterministic local keyword retrieval over evidence passages."""

import re
from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from scientia.evidence import Passage


@dataclass(frozen=True)
class RetrievalHit:
    """A passage and its distinct-query-token overlap score."""

    passage: Passage
    score: int


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.casefold()))


def retrieve(
    query: str,
    passages: Sequence[Passage],
    limit: int = 10,
) -> tuple[RetrievalHit, ...]:
    """Rank passages by distinct query-token overlap, preserving each record."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    if not query.strip():
        raise ValueError("query must not be blank")
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError("limit must be a positive integer")
    if limit <= 0:
        raise ValueError("limit must be a positive integer")

    query_tokens = _tokens(query)
    if not query_tokens:
        return ()

    hits: list[RetrievalHit] = []
    seen_passage_ids: set[tuple[UUID, UUID]] = set()
    for passage in passages:
        if not isinstance(passage, Passage):
            raise TypeError("passages must contain only Passage records")
        passage_identity = (passage.source_id, passage.passage_id)
        if passage_identity in seen_passage_ids:
            raise ValueError("passages must not contain duplicate passage identity")
        seen_passage_ids.add(passage_identity)
        score = len(query_tokens & _tokens(passage.text))
        if score:
            hits.append(RetrievalHit(passage=passage, score=score))

    hits.sort(
        key=lambda hit: (
            -hit.score,
            hit.passage.source_id,
            hit.passage.passage_id,
        )
    )
    return tuple(hits[:limit])
