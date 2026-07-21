"""Nautilus context-menu integration for PrintQueue."""

from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

from gi.repository import GObject, Nautilus

SUPPORTED_SUFFIXES = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".odt",
    ".ods",
    ".odp",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
}


class PrintQueueMenuProvider(GObject.GObject, Nautilus.MenuProvider):
    """Add selected local documents to the running PrintQueue instance."""

    def get_file_items(self, files):
        paths = self._local_supported_paths(files)
        if not paths:
            return []

        item = Nautilus.MenuItem(
            name="PrintQueueMenuProvider::add",
            label="Add to PrintQueue",
            tip="Add the selected files to the PrintQueue print list",
        )
        item.connect("activate", self._activate, paths)
        return [item]

    @staticmethod
    def _local_supported_paths(files) -> list[str]:
        paths: list[str] = []
        for file_info in files:
            parsed = urlparse(file_info.get_uri())
            if parsed.scheme != "file" or parsed.netloc not in {"", "localhost"}:
                return []
            path = unquote(parsed.path)
            if Path(path).suffix.lower() not in SUPPORTED_SUFFIXES:
                return []
            paths.append(path)
        return paths

    @staticmethod
    def _activate(_menu_item, paths: list[str]) -> None:
        subprocess.Popen(
            ["/usr/bin/printqueue", "--", *paths],
            close_fds=True,
            start_new_session=True,
        )
