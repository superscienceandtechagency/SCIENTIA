"""Local-only command-line access to SCIENTIA's research workflow."""

import argparse
import json
import sys
from collections.abc import Sequence
from uuid import uuid4

from scientia.pdf_ingestion import PdfIngestionError
from scientia.synthesis import ResearchQuestion
from scientia.workflow import prepare_research


def _nonblank(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("must not be blank")
    return value


def _positive_int(value: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if result <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Local-only development CLI; this is not a production-secure "
            "or multi-tenant interface."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser(
        "prepare",
        help="retrieve passages from explicitly selected local PDFs",
    )
    prepare.add_argument("--question", required=True, type=_nonblank)
    prepare.add_argument("--pdf", action="append", required=True, metavar="PATH")
    prepare.add_argument("--limit", default=10, type=_positive_int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the local-only command-line interface."""
    args = _build_parser().parse_args(argv)
    try:
        result = prepare_research(
            ResearchQuestion(uuid4(), args.question),
            args.pdf,
            limit=args.limit,
        )
    except PdfIngestionError as exc:
        print(
            f"scientia: PDF processing failed at {exc.stage}: {exc}",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(
            "scientia: unexpected processing failure "
            f"({type(exc).__name__}); no results were produced",
            file=sys.stderr,
        )
        return 1

    filenames = {
        item.source.source_id: item.original_filename
        for item in result.ingestion_results
    }
    output = {
        "hit_count": len(result.retrieval_hits),
        "hits": [
            {
                "rank": rank,
                "source": filenames[hit.passage.source_id],
                "page": (
                    hit.passage.location.page_start
                    if hit.passage.location is not None
                    else None
                ),
                "score": hit.score,
                "text": hit.passage.text,
            }
            for rank, hit in enumerate(result.retrieval_hits, start=1)
        ],
    }
    try:
        print(json.dumps(output, ensure_ascii=True, indent=2))
        sys.stdout.flush()
    except OSError:
        print("scientia: could not write results to standard output", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
