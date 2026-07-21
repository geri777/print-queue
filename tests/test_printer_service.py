from pathlib import Path
from unittest.mock import Mock

from printqueue.domain import PrintOptions
from printqueue.services.printer_service import PrinterService


def test_submit_builds_safe_cups_command(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}")
    run = Mock(return_value=Mock(returncode=0, stdout="request id is office-42\n", stderr=""))
    monkeypatch.setattr("subprocess.run", run)
    options = PrintOptions(
        printer="office",
        copies=2,
        duplex="two-sided-long-edge",
        media="A4",
        orientation="landscape",
    )
    job_id = PrinterService.submit(Path("/tmp/document with spaces.pdf"), options)
    command = run.call_args.args[0]
    assert command == [
        "lp",
        "-d",
        "office",
        "-n",
        "2",
        "-o",
        "sides=two-sided-long-edge",
        "-o",
        "media=A4",
        "-o",
        "orientation-requested=4",
        "--",
        "/tmp/document with spaces.pdf",
    ]
    assert job_id == "office-42"


def test_parse_modern_printer_capabilities():
    output = """PageSize/Media Size: *A4 A3 Letter
sides/2-Sided Printing: *one-sided two-sided-long-edge two-sided-short-edge
"""
    capabilities = PrinterService.parse_capabilities(output)
    assert capabilities.media == ("A4", "A3", "Letter")
    assert capabilities.duplex == (
        "one-sided",
        "two-sided-long-edge",
        "two-sided-short-edge",
    )


def test_parse_legacy_duplex_capabilities():
    capabilities = PrinterService.parse_capabilities(
        "Duplex/Duplex: *None DuplexNoTumble DuplexTumble\n"
    )
    assert capabilities.duplex == (
        "one-sided",
        "two-sided-long-edge",
        "two-sided-short-edge",
    )
