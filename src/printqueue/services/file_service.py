from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from printqueue.domain import FileKind, QueueItem

PDF_SUFFIXES = {".pdf"}
OFFICE_SUFFIXES = {
    ".docx",
    ".xlsx",
    ".pptx",
    ".doc",
    ".xls",
    ".ppt",
    ".odt",
    ".ods",
    ".odp",
    ".txt",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
SUPPORTED_SUFFIXES = PDF_SUFFIXES | OFFICE_SUFFIXES | IMAGE_SUFFIXES


class UnsupportedFileError(ValueError):
    pass


def classify(path: Path) -> FileKind:
    suffix = path.suffix.lower()
    if suffix in PDF_SUFFIXES:
        return FileKind.PDF
    if suffix in OFFICE_SUFFIXES:
        return FileKind.OFFICE
    if suffix in IMAGE_SUFFIXES:
        return FileKind.IMAGE
    raise UnsupportedFileError(f"Unsupported file type: {path.suffix or '(no extension)'}")


def inspect_file(raw_path: str | Path) -> QueueItem:
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a regular file: {path}")
    kind = classify(path)
    stat = path.stat()
    return QueueItem(path=path, kind=kind, size=stat.st_size, source_mtime_ns=stat.st_mtime_ns)


def inspect_files(paths: Iterable[str | Path]) -> tuple[list[QueueItem], list[str]]:
    items: list[QueueItem] = []
    errors: list[str] = []
    for path in paths:
        try:
            items.append(inspect_file(path))
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    return items, errors


def qt_file_filter() -> str:
    patterns = " ".join(f"*{suffix}" for suffix in sorted(SUPPORTED_SUFFIXES))
    return f"Supported documents ({patterns});;All files (*)"
