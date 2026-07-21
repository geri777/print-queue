from __future__ import annotations

from PySide6.QtCore import QSettings, QThread
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from printqueue.domain import ItemState, PrintOptions
from printqueue.file_model import FileTableModel
from printqueue.print_worker import PrintWorker
from printqueue.services.file_service import inspect_files, qt_file_filter
from printqueue.services.printer_service import PrinterService


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PrintQueue")
        self.setMinimumSize(860, 560)
        self.setAcceptDrops(True)
        self.settings = QSettings("PrintQueue", "PrintQueue")
        self.model = FileTableModel()
        self._thread: QThread | None = None
        self._worker: PrintWorker | None = None
        self._build_ui()
        self._restore_settings()
        self.refresh_printers()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 390)
        layout.addWidget(self.table, 1)

        file_buttons = QHBoxLayout()
        self.add_button = QPushButton("Add files …")
        self.remove_button = QPushButton("Remove")
        self.remove_all_button = QPushButton("Remove all")
        self.up_button = QPushButton("Move up")
        self.down_button = QPushButton("Move down")
        file_buttons.addWidget(self.add_button)
        file_buttons.addWidget(self.remove_button)
        file_buttons.addWidget(self.remove_all_button)
        file_buttons.addStretch()
        file_buttons.addWidget(self.up_button)
        file_buttons.addWidget(self.down_button)
        layout.addLayout(file_buttons)

        options_layout = QFormLayout()
        printer_row = QHBoxLayout()
        self.printer_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh")
        printer_row.addWidget(self.printer_combo, 1)
        printer_row.addWidget(self.refresh_button)
        options_layout.addRow("Printer:", printer_row)

        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 999)
        self.duplex_combo = QComboBox()
        self.duplex_combo.addItem("One-sided", "one-sided")
        self.duplex_combo.addItem("Two-sided (long edge)", "two-sided-long-edge")
        self.duplex_combo.addItem("Two-sided (short edge)", "two-sided-short-edge")
        self.media_combo = QComboBox()
        self.media_combo.addItems(["A4", "A3", "A5", "Letter", "Legal"])
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem("Portrait", "portrait")
        self.orientation_combo.addItem("Landscape", "landscape")

        compact = QHBoxLayout()
        compact.addWidget(QLabel("Copies:"))
        compact.addWidget(self.copies_spin)
        compact.addSpacing(20)
        compact.addWidget(QLabel("Duplex:"))
        compact.addWidget(self.duplex_combo, 1)
        compact.addSpacing(20)
        compact.addWidget(QLabel("Paper:"))
        compact.addWidget(self.media_combo)
        compact.addSpacing(20)
        compact.addWidget(QLabel("Orientation:"))
        compact.addWidget(self.orientation_combo)
        options_layout.addRow(compact)
        layout.addLayout(options_layout)

        self.status_label = QLabel("Drop files here or add them using the file dialog.")
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        self.print_button = QPushButton("Print")
        self.print_button.setDefault(True)
        action_row.addWidget(self.cancel_button)
        action_row.addWidget(self.print_button)
        layout.addLayout(action_row)
        self.setCentralWidget(root)

        self.add_button.clicked.connect(self._choose_files)
        self.remove_button.clicked.connect(self._remove_selected)
        self.remove_all_button.clicked.connect(self._remove_all)
        self.up_button.clicked.connect(lambda: self._move_selected(-1))
        self.down_button.clicked.connect(lambda: self._move_selected(1))
        self.refresh_button.clicked.connect(self.refresh_printers)
        self.printer_combo.currentIndexChanged.connect(self._refresh_capabilities)
        self.print_button.clicked.connect(self.start_print)
        self.cancel_button.clicked.connect(self._cancel_print)

    def add_paths(self, paths: list[str]) -> None:
        items, errors = inspect_files(paths)
        added = self.model.add_items(items)
        duplicates = len(items) - added
        parts = [f"{added} file(s) added"]
        if duplicates:
            parts.append(f"{duplicates} duplicate(s) ignored")
        if errors:
            parts.append(f"{len(errors)} error(s)")
            QMessageBox.warning(self, "Files could not be added", "\n".join(errors))
        self.status_label.setText(" · ".join(parts))
        self.print_button.setEnabled(
            bool(self.model.items) and bool(self.printer_combo.currentData())
        )

    def refresh_printers(self) -> None:
        previous = self.printer_combo.currentData() or self.settings.value("printer", "")
        printers = PrinterService.available_printers()
        self.printer_combo.clear()
        for printer in printers:
            label = f"{printer.name} (default)" if printer.is_default else printer.name
            self.printer_combo.addItem(label, printer.name)
        preferred = next(
            (i for i, printer in enumerate(printers) if printer.name == previous),
            next((i for i, printer in enumerate(printers) if printer.is_default), -1),
        )
        if preferred >= 0:
            self.printer_combo.setCurrentIndex(preferred)
        self.print_button.setEnabled(bool(printers) and bool(self.model.items))
        if not printers:
            self.printer_combo.addItem("No CUPS printers found", "")
        else:
            self._refresh_capabilities()

    def _refresh_capabilities(self) -> None:
        printer = self.printer_combo.currentData()
        if not printer:
            return
        previous_media = self.media_combo.currentText()
        previous_duplex = self.duplex_combo.currentData()
        capabilities = PrinterService.capabilities(printer)
        if capabilities.media:
            self.media_combo.clear()
            self.media_combo.addItems(capabilities.media)
            self.media_combo.setCurrentText(
                previous_media if previous_media in capabilities.media else capabilities.media[0]
            )
        labels = {
            "one-sided": "One-sided",
            "two-sided-long-edge": "Two-sided (long edge)",
            "two-sided-short-edge": "Two-sided (short edge)",
        }
        self.duplex_combo.clear()
        for value in capabilities.duplex:
            self.duplex_combo.addItem(labels[value], value)
        self._select_data(self.duplex_combo, previous_duplex)

    def start_print(self) -> None:
        if not self.model.items:
            QMessageBox.information(
                self, "Empty print queue", "Add at least one file before printing."
            )
            return
        printer = self.printer_combo.currentData()
        if not printer:
            QMessageBox.warning(self, "No printer", "No available printer was found.")
            return

        self.model.reset_statuses()
        options = PrintOptions(
            printer=printer,
            copies=self.copies_spin.value(),
            duplex=self.duplex_combo.currentData(),
            media=self.media_combo.currentText(),
            orientation=self.orientation_combo.currentData(),
        )
        self._thread = QThread(self)
        self._worker = PrintWorker(list(self.model.items), options)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.item_progress.connect(self._item_progress)
        self._worker.stage_changed.connect(self.status_label.setText)
        self._worker.succeeded.connect(self._print_succeeded)
        self._worker.failed.connect(self._print_failed)
        self._worker.cancelled.connect(
            lambda: self.status_label.setText("Print preparation cancelled.")
        )
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._print_finished)
        self._set_busy(True)
        self.progress.setRange(0, len(self.model.items))
        self.progress.setValue(0)
        self._thread.start()

    def _item_progress(self, row, state, message) -> None:
        self.model.update_status(row, state, message)
        self.progress.setValue(
            max(self.progress.value(), row + (1 if state is ItemState.DONE else 0))
        )
        self.status_label.setText(message)

    def _print_succeeded(self, job_id: str) -> None:
        self.progress.setValue(self.progress.maximum())
        message = f"Print job {job_id} was sent to the printer."
        self.status_label.setText(message)
        answer = QMessageBox.question(
            self,
            "Print job sent",
            f"{message}\n\nRemove the files from the list?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self._remove_all()
            self.status_label.setText(f"{message} The file list was cleared.")

    def _print_failed(self, message: str) -> None:
        self.status_label.setText("The print job failed.")
        QMessageBox.critical(self, "Print error", message)

    def _print_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_busy(False)

    def _cancel_print(self) -> None:
        if self._worker:
            self._worker.cancel()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Cancelling after the current processing step …")

    def _set_busy(self, busy: bool) -> None:
        for widget in (
            self.add_button,
            self.remove_button,
            self.remove_all_button,
            self.up_button,
            self.down_button,
            self.refresh_button,
            self.print_button,
            self.printer_combo,
            self.copies_spin,
            self.duplex_combo,
            self.media_combo,
            self.orientation_combo,
        ):
            widget.setEnabled(not busy)
        self.cancel_button.setVisible(busy)
        self.cancel_button.setEnabled(busy)
        self.progress.setVisible(busy)
        if not busy:
            self.print_button.setEnabled(
                bool(self.model.items) and bool(self.printer_combo.currentData())
            )

    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Add documents", "", qt_file_filter())
        if paths:
            self.add_paths(paths)

    def _remove_selected(self) -> None:
        rows = [index.row() for index in self.table.selectionModel().selectedRows()]
        self.model.remove_rows(rows)
        self.print_button.setEnabled(
            bool(self.model.items) and bool(self.printer_combo.currentData())
        )

    def _remove_all(self) -> None:
        self.model.remove_rows(list(range(len(self.model.items))))
        self.table.clearSelection()
        self.print_button.setEnabled(False)
        self.status_label.setText("The file list was cleared.")

    def _move_selected(self, offset: int) -> None:
        rows = [index.row() for index in self.table.selectionModel().selectedRows()]
        if len(rows) != 1:
            return
        destination = self.model.move_row(rows[0], offset)
        self.table.selectRow(destination)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self.add_paths(paths)
        event.acceptProposedAction()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._thread and self._thread.isRunning():
            QMessageBox.information(
                self, "Print job in progress", "Cancel the print job before closing PrintQueue."
            )
            event.ignore()
            return
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("printer", self.printer_combo.currentData() or "")
        self.settings.setValue("copies", self.copies_spin.value())
        self.settings.setValue("duplex", self.duplex_combo.currentData())
        self.settings.setValue("media", self.media_combo.currentText())
        self.settings.setValue("orientation", self.orientation_combo.currentData())
        super().closeEvent(event)

    def _restore_settings(self) -> None:
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self.copies_spin.setValue(int(self.settings.value("copies", 1)))
        self._select_data(self.duplex_combo, self.settings.value("duplex", "one-sided"))
        self.media_combo.setCurrentText(self.settings.value("media", "A4"))
        self._select_data(self.orientation_combo, self.settings.value("orientation", "portrait"))

    @staticmethod
    def _select_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)
