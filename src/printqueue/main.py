from __future__ import annotations

import argparse
import sys
from pathlib import Path

from printqueue import __version__


def parse_args(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="printqueue", description="Dokumente gesammelt drucken")
    parser.add_argument("files", nargs="*", help="Dateien, die zur Druckliste hinzugefügt werden")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(arguments)


def main() -> int:
    args = parse_args(sys.argv[1:])
    paths = [str(Path(path).expanduser().resolve()) for path in args.files]

    from PySide6.QtCore import QCoreApplication
    from PySide6.QtWidgets import QApplication, QMessageBox

    from printqueue.main_window import MainWindow
    from printqueue.single_instance import SingleInstance

    QCoreApplication.setApplicationName("PrintQueue")
    QCoreApplication.setOrganizationName("PrintQueue")
    application = QApplication(sys.argv[:1])
    application.setDesktopFileName("org.printqueue.PrintQueue")

    instance = SingleInstance()
    try:
        primary = instance.start_or_forward(paths)
    except RuntimeError as exc:
        QMessageBox.critical(None, "PrintQueue konnte nicht gestartet werden", str(exc))
        return 1
    if not primary:
        return 0

    window = MainWindow()

    def receive_paths(received: list[str]) -> None:
        window.add_paths(received)
        window.showNormal()
        window.raise_()
        window.activateWindow()

    instance.paths_received.connect(receive_paths)
    if paths:
        window.add_paths(paths)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
