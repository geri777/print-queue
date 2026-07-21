import threading
from pathlib import Path

import pytest

from printqueue.domain import FileKind, ItemState, PrintOptions, QueueItem
from printqueue.services.print_pipeline import PrintCancelled, PrintPipeline


class FakeConverter:
    def __init__(self):
        self.output_directories = []

    def convert(self, item, output_dir):
        self.output_directories.append(output_dir)
        target = output_dir / f"{item.path.stem}.pdf"
        target.write_bytes(b"fake")
        return target


class FakePrinter:
    def __init__(self):
        self.submitted = None

    def submit(self, pdf, options):
        self.submitted = (pdf, options)
        assert pdf.exists()
        return "printer-17"


def test_pipeline_converts_then_merges_and_submits(monkeypatch, tmp_path):
    sources = []
    for folder in ("a", "b"):
        directory = tmp_path / folder
        directory.mkdir()
        source = directory / "same.docx"
        source.write_bytes(b"office")
        sources.append(
            QueueItem(
                path=source, kind=FileKind.OFFICE, size=6, source_mtime_ns=source.stat().st_mtime_ns
            )
        )
    converter = FakeConverter()
    printer = FakePrinter()

    def fake_merge(pdfs, target):
        assert len(list(pdfs)) == 2
        target.write_bytes(b"merged")
        return target

    monkeypatch.setattr("printqueue.services.print_pipeline.merge_pdfs", fake_merge)
    updates = []
    result = PrintPipeline(converter, printer).run(
        sources,
        PrintOptions(printer="printer"),
        lambda *args: updates.append(args),
        lambda _message: None,
        threading.Event(),
    )
    assert result == "printer-17"
    assert converter.output_directories[0] != converter.output_directories[1]
    assert all(not directory.exists() for directory in converter.output_directories)
    assert printer.submitted is not None
    assert not printer.submitted[0].exists()
    assert [update[1] for update in updates] == [
        ItemState.PROCESSING,
        ItemState.DONE,
        ItemState.PROCESSING,
        ItemState.DONE,
    ]


def test_pipeline_honors_cancellation_before_work():
    event = threading.Event()
    event.set()
    item = QueueItem(path=Path("unused.pdf"), kind=FileKind.PDF, size=0)
    with pytest.raises(PrintCancelled):
        PrintPipeline(FakeConverter(), FakePrinter()).run(
            [item],
            PrintOptions(printer="printer"),
            lambda *_args: None,
            lambda _message: None,
            event,
        )
