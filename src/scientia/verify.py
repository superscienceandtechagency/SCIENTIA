"""Run SCIENTIA's canonical local verification checks."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECK_TIMEOUT_SECONDS = 600
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class _CheckResult:
    returncode: int | None
    stdout: str | None = None
    stderr: str | None = None
    failure_reason: str | None = None
    error_detail: str | None = None


def _run_check(
    name: str,
    command: list[str],
    *,
    run: CommandRunner,
    output: TextIO,
    capture_output: bool = False,
) -> _CheckResult:
    print(f"[RUN ] {name}", file=output, flush=True)
    try:
        result = run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=capture_output,
            text=True,
            timeout=CHECK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return _CheckResult(
            returncode=None,
            stdout=_as_text(exc.stdout),
            stderr=_as_text(exc.stderr),
            failure_reason="timed out",
            error_detail=f"exceeded {CHECK_TIMEOUT_SECONDS} seconds",
        )
    except OSError as exc:
        return _CheckResult(
            returncode=None,
            failure_reason="could not start command",
            error_detail=str(exc),
        )

    return _CheckResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _as_text(value: str | bytes | None) -> str | None:
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _is_unit_interval_metric(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0 <= value <= 1
    )


def _status(result: _CheckResult) -> str:
    if result.failure_reason is not None:
        status = f"FAIL ({result.failure_reason})"
        if result.error_detail:
            status += f": {result.error_detail}"
        return status
    if result.returncode:
        return f"FAIL (exit code {result.returncode})"
    return "PASS"


def _valid_evaluation_output(stdout: str | None) -> bool:
    if stdout is None:
        return False
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError:
        return False
    if not isinstance(report, dict):
        return False
    report_fields = {
        "benchmark",
        "k",
        "queries",
        "mean_precision_at_k",
        "mean_recall_at_k",
        "mean_reciprocal_rank",
        "mrr_included_queries",
        "mrr_excluded_queries",
    }
    if not report_fields.issubset(report):
        return False
    queries = report.get("queries")
    if not isinstance(queries, list) or not queries:
        return False
    query_fields = {
        "query_id",
        "query",
        "relevance_rationale",
        "retrieved_ids",
        "ranked_results",
        "precision_at_k",
        "recall_at_k",
        "reciprocal_rank",
        "analysis_status",
        "missed_relevant_ids",
        "irrelevant_retrieved_ids",
        "relevant_rank_positions",
        "ranking_errors",
    }
    if any(
        not isinstance(query, dict)
        or not query_fields.issubset(query)
        or not isinstance(query["query_id"], str)
        or not isinstance(query["query"], str)
        or not isinstance(query["relevance_rationale"], str)
        or not isinstance(query["retrieved_ids"], list)
        or not isinstance(query["ranked_results"], list)
        or not isinstance(query["analysis_status"], str)
        for query in queries
    ):
        return False
    aggregate_metrics = (
        report.get("mean_precision_at_k"),
        report.get("mean_recall_at_k"),
        report.get("mean_reciprocal_rank"),
    )
    if any(
        not _is_unit_interval_metric(value)
        for value in (
            query["precision_at_k"]
            for query in queries
        )
    ):
        return False
    if not _is_unit_interval_metric(aggregate_metrics[0]):
        return False
    optional_query_metrics = (
        metric
        for query in queries
        for metric in (query["recall_at_k"], query["reciprocal_rank"])
        if metric is not None
    )
    if any(not _is_unit_interval_metric(value) for value in optional_query_metrics):
        return False
    return (
        report.get("benchmark") == "synthetic-lexical-v2"
        and type(report.get("k")) is int
        and report["k"] > 0
        and all(
            value is None or _is_unit_interval_metric(value)
            for value in aggregate_metrics[1:]
        )
        and all(
            type(report.get(field)) is int and report[field] >= 0
            for field in ("mrr_included_queries", "mrr_excluded_queries")
        )
    )


def run_verification(
    *,
    run: CommandRunner | None = None,
    output: TextIO | None = None,
) -> int:
    """Run every local release check and return nonzero if any check fails."""
    command_runner = run or subprocess.run
    report = output or sys.stdout
    failed = False

    checks = (
        (
            "full test suite",
            ["uv", "run", "--locked", "pytest"],
        ),
        (
            "Ruff",
            ["uv", "run", "--locked", "ruff", "check", "."],
        ),
        (
            "lockfile consistency",
            ["uv", "lock", "--check"],
        ),
    )
    for name, command in checks:
        result = _run_check(name, command, run=command_runner, output=report)
        passed = result.failure_reason is None and result.returncode == 0
        failed |= not passed
        print(f"[{_status(result)}] {name}", file=report, flush=True)

    with tempfile.TemporaryDirectory(prefix="scientia-verify-build-") as build_dir:
        result = _run_check(
            "package build",
            ["uv", "build", "--out-dir", build_dir],
            run=command_runner,
            output=report,
        )
    passed = result.failure_reason is None and result.returncode == 0
    failed |= not passed
    print(f"[{_status(result)}] package build", file=report, flush=True)

    evaluation_command = [
        "uv",
        "run",
        "--locked",
        "python",
        "-m",
        "scientia.evaluation",
    ]
    first = _run_check(
        "synthetic evaluation (run 1)",
        evaluation_command,
        run=command_runner,
        output=report,
        capture_output=True,
    )
    second = _run_check(
        "synthetic evaluation (run 2)",
        evaluation_command,
        run=command_runner,
        output=report,
        capture_output=True,
    )
    executions_passed = all(
        result.failure_reason is None and result.returncode == 0
        for result in (first, second)
    )
    outputs_valid = all(
        _valid_evaluation_output(result.stdout) for result in (first, second)
    )
    passed = executions_passed and outputs_valid and first.stdout == second.stdout
    failed |= not passed
    if passed:
        state = "PASS"
    elif not executions_passed:
        details = "; ".join(
            f"run {index}: {_status(result).removeprefix('FAIL (').removesuffix(')')}"
            if result.failure_reason is not None or result.returncode != 0
            else f"run {index}: passed"
            for index, result in enumerate((first, second), start=1)
        )
        state = f"FAIL ({details})"
        for result in (first, second):
            if result.stderr:
                print(result.stderr, file=report, end="", flush=True)
    elif not outputs_valid:
        state = "FAIL (invalid evaluation output)"
    else:
        state = "FAIL (outputs differ)"
    print(f"[{state}] deterministic synthetic evaluation", file=report, flush=True)

    return int(failed)


def main() -> int:
    """CLI entry point for canonical local verification."""
    return run_verification()


if __name__ == "__main__":
    raise SystemExit(main())
