import json
import subprocess

import pytest

from report import report_info

# What chart-verifier actually writes to stdout when the report's digest does
# not match its content. The lowercase "digest" is the detail #539 turned on.
SHA_MISMATCH_OUTPUT = (
    "error executing command: digest in report did not match report content\n"
)


@pytest.fixture
def errors_file(tmp_path, monkeypatch):
    """Path to the errors file write_error_log records, which the submitter reads.

    write_error_log writes an "errors" file under WORKFLOW_WORKING_DIRECTORY,
    and build.yml renders that file verbatim into the PR comment. Pointing it
    at a temp dir lets a test assert on the exact text a submitter would see.
    """
    monkeypatch.setenv("WORKFLOW_WORKING_DIRECTORY", str(tmp_path))
    # _get_report_info reaches chart-verifier through docker when VERIFIER_IMAGE
    # is set and through subprocess.run otherwise. These tests stub
    # subprocess.run, so unset the variable to keep them off the docker path if
    # it happens to be set in the environment running pytest.
    monkeypatch.delenv("VERIFIER_IMAGE", raising=False)
    return tmp_path / "errors"


def fake_verifier_output(monkeypatch, stdout):
    """Makes the chart-verifier subprocess return stdout."""

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr=b"")

    monkeypatch.setattr(report_info.subprocess, "run", fake_run)


def test_sha_mismatch_reports_a_plain_message(monkeypatch, errors_file):
    fake_verifier_output(monkeypatch, SHA_MISMATCH_OUTPUT.encode())

    with pytest.raises(SystemExit) as excinfo:
        report_info.get_report_digests(report_path="report.yaml")

    assert excinfo.value.code == 1
    assert errors_file.read_text() == f"[ERROR] {report_info.SHA_ERROR}\n"


def test_unparseable_output_does_not_leak_the_exception(monkeypatch, errors_file):
    fake_verifier_output(monkeypatch, b"not json at all")

    with pytest.raises(SystemExit) as excinfo:
        report_info.get_report_digests(report_path="report.yaml")

    assert excinfo.value.code == 1
    errors = errors_file.read_text()
    assert "not json at all" in errors
    # The submitter should never see the Python exception, nor the "/n" that used
    # to be written in place of a newline. See issue #539.
    assert "JSONDecodeError" not in errors
    assert "type(err)" not in errors
    assert "/n" not in errors


def test_undecodable_output_does_not_traceback(monkeypatch, errors_file):
    fake_verifier_output(monkeypatch, b"\xff\xfe not utf-8")

    with pytest.raises(SystemExit) as excinfo:
        report_info.get_report_digests(report_path="report.yaml")

    assert excinfo.value.code == 1
    assert "JSONDecodeError" not in errors_file.read_text()


def test_undecodable_output_is_never_silently_repaired(monkeypatch, errors_file):
    # Valid JSON apart from one undecodable byte inside the digest. Decoding
    # with errors="replace" would substitute U+FFFD, parse cleanly and return a
    # corrupted digest, which would then be published.
    fake_verifier_output(monkeypatch, b'{"digests": {"chart": "sha256:\xc3bcdef"}}')

    with pytest.raises(SystemExit) as excinfo:
        report_info.get_report_digests(report_path="report.yaml")

    assert excinfo.value.code == 1


def test_missing_section_reports_a_plain_message(monkeypatch, errors_file):
    fake_verifier_output(monkeypatch, json.dumps({"metadata": {}}).encode())

    with pytest.raises(SystemExit) as excinfo:
        report_info.get_report_digests(report_path="report.yaml")

    assert excinfo.value.code == 1
    errors = errors_file.read_text()
    assert "no digests section" in errors
    assert "Traceback" not in errors


def test_valid_output_is_returned(monkeypatch, errors_file):
    digests = {"chart": "sha256:abc", "package": "sha256:def"}
    fake_verifier_output(monkeypatch, json.dumps({"digests": digests}).encode())

    assert report_info.get_report_digests(report_path="report.yaml") == digests
