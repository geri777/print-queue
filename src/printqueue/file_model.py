from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from printqueue.domain import ItemState, QueueItem


class FileTableModel(QAbstractTableModel):
    HEADERS = ("File", "Type", "Size", "Status")

    def __init__(self) -> None:
        super().__init__()
        self.items: list[QueueItem] = []

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: B008, N802
        return 0 if parent.isValid() else len(self.items)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: B008, N802
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # noqa: N802
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.items):
            return None
        item = self.items[index.row()]
        if role == Qt.DisplayRole:
            values = (
                item.path.name,
                item.kind.value,
                self._format_size(item.size),
                item.display_status,
            )
            return values[index.column()]
        if role == Qt.ToolTipRole:
            return str(item.path) if index.column() == 0 else item.display_status
        if role == Qt.UserRole:
            return str(item.path)
        return None

    def add_items(self, items: list[QueueItem]) -> int:
        known = {item.path for item in self.items}
        unique = [item for item in items if item.path not in known]
        if not unique:
            return 0
        first = len(self.items)
        self.beginInsertRows(QModelIndex(), first, first + len(unique) - 1)
        self.items.extend(unique)
        self.endInsertRows()
        return len(unique)

    def remove_rows(self, rows: list[int]) -> None:
        for row in sorted(set(rows), reverse=True):
            if 0 <= row < len(self.items):
                self.beginRemoveRows(QModelIndex(), row, row)
                del self.items[row]
                self.endRemoveRows()

    def move_row(self, row: int, offset: int) -> int:
        destination = row + offset
        if not (0 <= row < len(self.items) and 0 <= destination < len(self.items)):
            return row
        destination_child = destination if offset < 0 else destination + 1
        self.beginMoveRows(QModelIndex(), row, row, QModelIndex(), destination_child)
        self.items.insert(destination, self.items.pop(row))
        self.endMoveRows()
        return destination

    def update_status(self, row: int, state: ItemState, message: str) -> None:
        if not 0 <= row < len(self.items):
            return
        self.items[row].state = state
        self.items[row].message = message
        status = self.index(row, 3)
        self.dataChanged.emit(status, status, [Qt.DisplayRole, Qt.ToolTipRole])

    def reset_statuses(self) -> None:
        for item in self.items:
            item.state = ItemState.READY
            item.message = ""
        if self.items:
            self.dataChanged.emit(self.index(0, 3), self.index(len(self.items) - 1, 3))

    @staticmethod
    def _format_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KiB", "MiB", "GiB"):
            if value < 1024 or unit == "GiB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024
        return f"{size} B"
