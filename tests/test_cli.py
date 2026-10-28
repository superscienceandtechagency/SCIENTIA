import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from scientia import cli


def _pdf_bytes(text: str) -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET\n".encode()
    objects.append(
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"endstream"
    )

    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{object_number} 0 obj\n".encode())
        result.extend(body)
        result.extend(b"\nendobj\n")
    xref_offset = len(result)
    result.extend(f"xref\n0 {len(offsets)}\n".encode())
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n".encode()
    )
    result.extend(f"startxref\n{xref_offset}\n%%EOF\n".encode())
    return bytes(result)


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scientia.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def test_cli_runs_local_workflow_and_prints_ranked_excerpts(tmp_path):
    pdf_path = tmp_path / "research.pdf"
    pdf_path.write_bytes(
        _pdf_bytes("Intervention X reduced symptom severity in the study.")
    )

    result = _run_cli(
        "prepare",
        "--question",
        "Intervention symptom",
        "--pdf",
        str(pdf_path),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    output = json.loads(result.stdout)
    assert output["hit_count"] == 1
    assert output["hits"] == [
        {
            "rank": 1,
            "source": "research.pdf",
            "page": 1,
            "score": 2,
            "text": "Intervention X reduced symptom severity in the study.",
        }
    ]


def test_cli_accepts_unicode_question_and_keeps_output_valid_json(tmp_path):
    pdf_path = tmp_path / "research.pdf"
    pdf_path.write_bytes(_pdf_bytes("Intervention reduces symptoms."))

    result = _run_cli(
        "prepare",
        "--question",
        "Intervention café — Ω",
        "--pdf",
        str(pdf_path),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    output = json.loads(result.stdout)
    assert output["hits"][0]["source"] == "research.pdf"
    assert output["hits"][0]["page"] == 1


def test_cli_help_describes_local_only_command():
    result = _run_cli("--help")

    assert result.returncode == 0
    assert "local-only" in result.stdout.lower()
    assert "prepare" in result.stdout


def test_cli_rejects_missing_question_and_pdf():
    result = _run_cli("prepare")

    assert result.returncode == 2
    assert "error:" in result.stderr
    assert result.stdout == ""


def test_cli_rejects_non_positive_limit():
    result = _run_cli(
        "prepare",
        "--question",
        "research question",
        "--pdf",
        "unused.pdf",
        "--limit",
        "0",
    )

    assert result.returncode == 2
    assert "positive integer" in result.stderr


def test_cli_reports_pdf_processing_failure_without_content(tmp_path):
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_text("private input that is not a PDF", encoding="utf-8")

    result = _run_cli(
        "prepare",
        "--question",
        "research question",
        "--pdf",
        str(pdf_path),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "scientia:" in result.stderr
    assert "private input" not in result.stderr


def test_cli_rejects_missing_file_with_nonzero_exit(tmp_path):
    missing_path = Path(tmp_path) / "missing.pdf"

    result = _run_cli(
        "prepare",
        "--question",
        "research question",
        "--pdf",
        str(missing_path),
    )

    assert result.returncode == 1
    assert "scientia:" in result.stderr
    assert "missing.pdf" not in result.stderr


def test_cli_reports_unreadable_file_without_absolute_path(
    monkeypatch,
    capsys,
    tmp_path,
):
    pdf_path = tmp_path / "private" / "unreadable.pdf"
    pdf_path.parent.mkdir()
    pdf_path.write_bytes(_pdf_bytes("Sensitive source text."))
    original_open = Path.open

    def deny_pdf_read(path, *args, **kwargs):
        if path == pdf_path and args and args[0] == "rb":
            raise PermissionError("permission denied")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", deny_pdf_read)

    result = cli.main(
        [
            "prepare",
            "--question",
            "research question",
            "--pdf",
            str(pdf_path),
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert "could not read input file" in captured.err.lower()
    assert str(pdf_path) not in captured.err


def test_cli_sanitizes_unexpected_processing_exception(monkeypatch, capsys):
    def fail_processing(*args, **kwargs):
        raise RuntimeError("private document text at /private/research.pdf")

    monkeypatch.setattr(cli, "prepare_research", fail_processing)

    result = cli.main(
        [
            "prepare",
            "--question",
            "research question",
            "--pdf",
            "research.pdf",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert "unexpected processing failure" in captured.err.lower()
    assert "RuntimeError" in captured.err
    assert "private document text" not in captured.err
    assert "/private/research.pdf" not in captured.err


def test_cli_reports_stdout_write_failure_as_nonzero(monkeypatch, capsys):
    class BrokenStdout:
        def write(self, value):
            raise OSError("disk full")

        def flush(self):
            return None

    monkeypatch.setattr(
        cli,
        "prepare_research",
        lambda *args, **kwargs: SimpleNamespace(
            ingestion_results=(),
            retrieval_hits=(),
        ),
    )
    monkeypatch.setattr(sys, "stdout", BrokenStdout())

    result = cli.main(
        [
            "prepare",
            "--question",
            "research question",
            "--pdf",
            "research.pdf",
        ]
    )

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert "could not write results" in captured.err.lower()
