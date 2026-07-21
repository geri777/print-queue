from __future__ import annotations

import tempfile
import threading
from collections.abc import Callable, Sequence
from pathlib import Path

from printqueue.domain import ItemState, PrintOptions, QueueItem
from printqueue.services.conversion_service import ConversionService
from printqueue.services.pdf_service import merge_pdfs
from printqueue.services.printer_service import PrinterService

ProgressCallback = Callable[[int, ItemState, str], None]
StageCallback = Callable[[str], None]


class PrintCancelled(RuntimeError):
    pass


class PrintPipeline:
    def __init__(
        self,
        converter: ConversionService | None = None,
        printer: PrinterService | None = None,
    ) -> None:
        self.converter = converter or ConversionService()
        self.printer = printer or PrinterService()

    def run(
        self,
        items: Sequence[QueueItem],
        options: PrintOptions,
        progress: ProgressCallback,
        stage: StageCallback,
        cancelled: threading.Event,
    ) -> str:
        if not items:
            raise ValueError("The print queue is empty.")

        with tempfile.TemporaryDirectory(prefix="printqueue-") as temp_name:
            temp_dir = Path(temp_name)
            pdfs: list[Path] = []
            for index, item in enumerate(items):
                self._check_cancelled(cancelled)
                progress(index, ItemState.PROCESSING, f"Converting {index + 1} of {len(items)}")
                item_dir = temp_dir / f"item-{index:04d}"
                item_dir.mkdir()
                try:
                    pdfs.append(self.converter.convert(item, item_dir))
                except Exception as exc:
                    progress(index, ItemState.ERROR, str(exc))
                    raise
                progress(index, ItemState.DONE, "Ready to print")

            self._check_cancelled(cancelled)
            stage("Merging documents …")
            merged = merge_pdfs(pdfs, temp_dir / "print-job.pdf")
            self._check_cancelled(cancelled)
            stage("Submitting print job to CUPS …")
            return self.printer.submit(merged, options)

    @staticmethod
    def _check_cancelled(cancelled: threading.Event) -> None:
        if cancelled.is_set():
            raise PrintCancelled("Print preparation was cancelled.")
