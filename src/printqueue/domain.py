from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FileKind(str, Enum):
    PDF = "PDF"
    OFFICE = "Office"
    IMAGE = "Bild"


class ItemState(str, Enum):
    READY = "Bereit"
    PROCESSING = "Wird verarbeitet"
    DONE = "Fertig"
    ERROR = "Fehler"


@dataclass(slots=True)
class QueueItem:
    path: Path
    kind: FileKind
    size: int
    state: ItemState = ItemState.READY
    message: str = ""
    source_mtime_ns: int = field(default=0, repr=False)

    @property
    def display_status(self) -> str:
        return self.message or self.state.value


@dataclass(frozen=True, slots=True)
class PrintOptions:
    printer: str
    copies: int = 1
    duplex: str = "one-sided"
    media: str = "A4"
    orientation: str = "portrait"


@dataclass(frozen=True, slots=True)
class Printer:
    name: str
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class PrinterCapabilities:
    media: tuple[str, ...] = ()
    duplex: tuple[str, ...] = ("one-sided",)
