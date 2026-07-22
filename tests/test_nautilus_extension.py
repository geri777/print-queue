from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock


class GObjectBase:
    pass


class MenuProvider:
    pass


class FileInfo:
    def __init__(self, uri: str) -> None:
        self._uri = uri

    def get_uri(self) -> str:
        return self._uri


def load_extension(monkeypatch):
    gi = ModuleType("gi")
    repository = ModuleType("gi.repository")
    repository.GObject = SimpleNamespace(GObject=GObjectBase)
    repository.Nautilus = SimpleNamespace(MenuProvider=MenuProvider, MenuItem=Mock)
    monkeypatch.setitem(sys.modules, "gi", gi)
    monkeypatch.setitem(sys.modules, "gi.repository", repository)
    path = Path(__file__).parents[1] / "resources/nautilus/printqueue.py"
    spec = importlib.util.spec_from_file_location("printqueue_nautilus_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_nautilus_extension_accepts_supported_local_files(monkeypatch):
    module = load_extension(monkeypatch)
    files = [
        FileInfo("file:///tmp/first%20file.pdf"),
        FileInfo("file://localhost/tmp/second.odt"),
        FileInfo("file:///tmp/notes.txt"),
    ]
    assert module.PrintQueueMenuProvider._local_supported_paths(files) == [
        "/tmp/first file.pdf",
        "/tmp/second.odt",
        "/tmp/notes.txt",
    ]


def test_nautilus_extension_rejects_remote_or_unsupported_files(monkeypatch):
    module = load_extension(monkeypatch)
    provider = module.PrintQueueMenuProvider
    assert provider._local_supported_paths([FileInfo("smb://server/share/file.pdf")]) == []
    assert provider._local_supported_paths([FileInfo("file:///tmp/archive.zip")]) == []


def test_nautilus_extension_launches_shared_application(monkeypatch):
    module = load_extension(monkeypatch)
    popen = Mock()
    monkeypatch.setattr(module.subprocess, "Popen", popen)
    module.PrintQueueMenuProvider._activate(None, ["/tmp/a.pdf", "/tmp/b.docx"])
    popen.assert_called_once_with(
        ["/usr/bin/printqueue", "--", "/tmp/a.pdf", "/tmp/b.docx"],
        close_fds=True,
        start_new_session=True,
    )
