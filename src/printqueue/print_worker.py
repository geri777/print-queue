from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal, Slot

from printqueue.domain import ItemState, PrintOptions, QueueItem
from printqueue.services.print_pipeline import PrintCancelled, PrintPipeline


class PrintWorker(QObject):
    item_progress = Signal(int, object, str)
    stage_changed = Signal(str)
    succeeded = Signal(str)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()

    def __init__(self, items: list[QueueItem], options: PrintOptions) -> None:
        super().__init__()
        self.items = items
        self.options = options
        self._cancel_event = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            job_id = PrintPipeline().run(
                self.items,
                self.options,
                self._progress,
                self.stage_changed.emit,
                self._cancel_event,
            )
        except PrintCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(job_id)
        finally:
            self.finished.emit()

    @Slot()
    def cancel(self) -> None:
        self._cancel_event.set()

    def _progress(self, index: int, state: ItemState, message: str) -> None:
        self.item_progress.emit(index, state, message)
