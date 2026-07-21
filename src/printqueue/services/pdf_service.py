from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


class PdfMergeError(RuntimeError):
    pass


def merge_pdfs(sources: Iterable[Path], target: Path) -> Path:
    from pypdf import PdfWriter

    writer = PdfWriter()
    try:
        for source in sources:
            writer.append(str(source))
        if not writer.pages:
            raise PdfMergeError("No printable PDF pages are available.")
        with target.open("wb") as output:
            writer.write(output)
    except PdfMergeError:
        raise
    except Exception as exc:
        raise PdfMergeError(f"The PDF files could not be merged: {exc}") from exc
    finally:
        writer.close()
    return target
