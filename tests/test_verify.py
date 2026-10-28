import json
import subprocess
from io import StringIO
from pathlib import Path

import pytest

from scientia.verify import run_verification


def _evaluation_output(precision: float = 0.5) -> str:
    return json.dumps(
        {
            "benchmark": "synthetic-lexical-v2",
            "k": 3,
            "queries": [
                {
                    "query_id": "synthetic-query",
                    "query": "a test query",
                    "relevance_rationale": "A synthetic relevance judgment.",
                    "retrieved_ids": [],
                    "ranked_results": [],
                    "precision_at_k": precision,
                    "recall_at_k": 0.4,
                    "reciprocal_rank": 0.6,
                    "analysis_status": "judged",
                    "missed_relevant_ids": [],
                    "irrelevant_retrieved_ids": [],
                    "relevant_rank_positions": [],
                    "ranking_errors": [],
                }
            ],
            "mean_precision_at_k": precision,
            "mean_recall_at_k": 0.4,
            "mean_reciprocal_rank": 0.6,
            "mrr_included_queries": 1,
            "mrr_excluded_queries": 0,
        }
    )


def test_verification_reports_each_check_and_propagates_failure():
    commands = []

    def run(command, **kwargs):
        commands.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            1 if command[:3] == ["uv", "run", "--locked"]
            and command[3:5] == ["ruff", "check"] else 0,
            stdout=_evaluation_output() if kwargs.get("capture_output") else None,
        )

    output = StringIO()

    result = run_verification(run=run, output=output)

    report = output.getvalue()
    assert result == 1
    assert "[PASS] full test suite" in report
    assert "[FAIL (exit code 1)] Ruff" in report
    assert "[PASS] lockfile consistency" in report
    assert "[PASS] package build" in report
    assert "[PASS] deterministic synthetic evaluation" in report
    assert sum(
        command[-2:] == ["-m", "scientia.evaluation"]
        for command, _ in commands
    ) == 2


def test_verification_fails_when_synthetic_outputs_differ():
    evaluation_runs = 0

    def run(command, **kwargs):
        nonlocal evaluation_runs
        if command[-2:] == ["-m", "scientia.evaluation"]:
            evaluation_runs += 1
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=_evaluation_output(0.4 + evaluation_runs / 10),
            )
        return subprocess.CompletedProcess(command, 0)

    output = StringIO()

    result = run_verification(run=run, output=output)

    assert result == 1
    assert "[FAIL (outputs differ)] deterministic synthetic evaluation" in (
        output.getvalue()
    )


def test_verification_reports_missing_executable_and_continues():
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        if command[-1:] == ["pytest"]:
            raise FileNotFoundError("uv executable not found")
        if command[-2:] == ["-m", "scientia.evaluation"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=_evaluation_output(),
            )
        return subprocess.CompletedProcess(command, 0)

    output = StringIO()

    result = run_verification(run=run, output=output)

    report = output.getvalue()
    assert result == 1
    assert "[FAIL (could not start command): uv executable not found]" in report
    assert "uv executable not found" in report
    assert "[PASS] Ruff" in report
    assert "[PASS] lockfile consistency" in report
    assert "[PASS] package build" in report
    assert len(commands) == 6


def test_verification_reports_timeout_and_applies_a_timeout():
    def run(command, **kwargs):
        assert kwargs["timeout"] > 0
        if command[-1:] == ["pytest"]:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        if command[-2:] == ["-m", "scientia.evaluation"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=_evaluation_output(),
            )
        return subprocess.CompletedProcess(command, 0)

    output = StringIO()

    result = run_verification(run=run, output=output)

    assert result == 1
    assert "[FAIL (timed out): exceeded 600 seconds] full test suite" in (
        output.getvalue()
    )


@pytest.mark.parametrize("malformed_output", ["not JSON", "{}"])
def test_verification_rejects_identical_malformed_evaluation_output(
    malformed_output,
):
    def run(command, **kwargs):
        if command[-2:] == ["-m", "scientia.evaluation"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=malformed_output,
            )
        return subprocess.CompletedProcess(command, 0)

    output = StringIO()

    result = run_verification(run=run, output=output)

    assert result == 1
    assert "[FAIL (invalid evaluation output)] deterministic synthetic evaluation" in (
        output.getvalue()
    )


def test_verification_cleans_build_directory_after_build_failure():
    build_directories: list[Path] = []

    def run(command, **kwargs):
        if command[1:2] == ["build"]:
            build_directory = Path(command[command.index("--out-dir") + 1])
            assert build_directory.is_dir()
            build_directories.append(build_directory)
            return subprocess.CompletedProcess(command, 1)
        if command[-2:] == ["-m", "scientia.evaluation"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=_evaluation_output(),
            )
        return subprocess.CompletedProcess(command, 0)

    output = StringIO()

    result = run_verification(run=run, output=output)

    assert result == 1
    assert "[FAIL (exit code 1)] package build" in output.getvalue()
    assert len(build_directories) == 1
    assert not build_directories[0].exists()


def test_verification_reports_evaluation_failure_details():
    evaluation_runs = 0

    def run(command, **kwargs):
        nonlocal evaluation_runs
        if command[-2:] == ["-m", "scientia.evaluation"]:
            evaluation_runs += 1
            if evaluation_runs == 1:
                return subprocess.CompletedProcess(
                    command,
                    2,
                    stdout="",
                    stderr="synthetic evaluation failed",
                )
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=_evaluation_output(),
            )
        return subprocess.CompletedProcess(command, 0)

    output = StringIO()

    result = run_verification(run=run, output=output)

    report = output.getvalue()
    assert result == 1
    assert "[FAIL (run 1: exit code 2; run 2: passed)]" in report
    assert "synthetic evaluation failed" in report


@pytest.mark.parametrize(
    "invalid_precision",
    [1.1, 10**4000],
    ids=["above-one", "very-large-integer"],
)
def test_verification_rejects_out_of_range_evaluation_metrics(invalid_precision):
    invalid_output = _evaluation_output(invalid_precision)

    def run(command, **kwargs):
        if command[-2:] == ["-m", "scientia.evaluation"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=invalid_output,
            )
        return subprocess.CompletedProcess(command, 0)

    output = StringIO()

    result = run_verification(run=run, output=output)

    assert result == 1
    assert "[FAIL (invalid evaluation output)]" in output.getvalue()
