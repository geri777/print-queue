from pathlib import Path

import pytest

from printqueue.domain import FileKind
from printqueue.services.file_service import (
    UnsupportedFileError,
    classify,
    inspect_file,
    inspect_files,
)


@pytest.mark.parametrize(
    ("name", "kind"),
    [
        ("document.PDF", FileKind.PDF),
        ("text.docx", FileKind.OFFICE),
        ("sheet.XLSX", FileKind.OFFICE),
        ("photo.jpeg", FileKind.IMAGE),
        ("scan.TIFF", FileKind.IMAGE),
    ],
)
def test_classify_supported_suffixes(name, kind):
    assert classify(Path(name)) is kind


def test_classify_rejects_unknown_suffix():
    with pytest.raises(UnsupportedFileError):
        classify(Path("archive.zip"))


def test_inspect_file_collects_metadata(tmp_path):
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"pdf")
    item = inspect_file(source)
    assert item.path == source.resolve()
    assert item.size == 3
    assert item.kind is FileKind.PDF
    assert item.source_mtime_ns > 0


def test_inspect_files_returns_valid_items_and_errors(tmp_path):
    source = tmp_path / "sample.png"
    source.write_bytes(b"image")
    items, errors = inspect_files([source, tmp_path / "missing.pdf"])
    assert [item.path for item in items] == [source.resolve()]
    assert len(errors) == 1
    assert "nicht gefunden" in errors[0]
