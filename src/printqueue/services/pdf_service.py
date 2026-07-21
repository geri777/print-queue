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
            raise PdfMergeError("Es sind keine druckbaren PDF-Seiten vorhanden.")
        with target.open("wb") as output:
            writer.write(output)
    except PdfMergeError:
        raise
    except Exception as exc:
        raise PdfMergeError(f"PDFs konnten nicht zusammengeführt werden: {exc}") from exc
    finally:
        writer.close()
    return target
