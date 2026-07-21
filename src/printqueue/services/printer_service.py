from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from printqueue.domain import Printer, PrinterCapabilities, PrintOptions


class PrinterError(RuntimeError):
    pass


_JOB_ID = re.compile(r"(?:request id is|Anfrage-ID ist)\s+([^\s]+)", re.IGNORECASE)


class PrinterService:
    @staticmethod
    def available_printers() -> list[Printer]:
        if not shutil.which("lpstat"):
            return []
        printers_result = subprocess.run(
            ["lpstat", "-p"], capture_output=True, text=True, check=False, timeout=10
        )
        default_result = subprocess.run(
            ["lpstat", "-d"], capture_output=True, text=True, check=False, timeout=10
        )
        default = (
            default_result.stdout.rsplit(":", 1)[-1].strip()
            if default_result.returncode == 0
            else ""
        )
        names: list[str] = []
        for line in printers_result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].lower() in {"printer", "drucker"}:
                names.append(parts[1])
        return [Printer(name=name, is_default=name == default) for name in names]

    @staticmethod
    def capabilities(printer: str) -> PrinterCapabilities:
        if not printer or not shutil.which("lpoptions"):
            return PrinterCapabilities()
        result = subprocess.run(
            ["lpoptions", "-p", printer, "-l"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if result.returncode:
            return PrinterCapabilities()
        return PrinterService.parse_capabilities(result.stdout)

    @staticmethod
    def parse_capabilities(output: str) -> PrinterCapabilities:
        media: list[str] = []
        duplex: list[str] = []
        legacy_duplex = {
            "None": "one-sided",
            "DuplexNoTumble": "two-sided-long-edge",
            "DuplexTumble": "two-sided-short-edge",
        }
        for line in output.splitlines():
            if ":" not in line:
                continue
            key, values_text = line.split(":", 1)
            option = key.split("/", 1)[0].strip().lower()
            values = [value.lstrip("*") for value in values_text.split()]
            if option in {"pagesize", "media"}:
                media = values
            elif option == "sides":
                duplex = [
                    value
                    for value in values
                    if value in {"one-sided", "two-sided-long-edge", "two-sided-short-edge"}
                ]
            elif option == "duplex" and not duplex:
                duplex = [legacy_duplex[value] for value in values if value in legacy_duplex]
        return PrinterCapabilities(
            media=tuple(dict.fromkeys(media)),
            duplex=tuple(dict.fromkeys(duplex)) or ("one-sided",),
        )

    @staticmethod
    def submit(pdf: Path, options: PrintOptions) -> str:
        if not shutil.which("lp"):
            raise PrinterError("CUPS-Clientprogramm 'lp' ist nicht installiert oder nicht im PATH.")
        if not options.printer:
            raise PrinterError("Es wurde kein Drucker ausgewählt.")

        command = [
            "lp",
            "-d",
            options.printer,
            "-n",
            str(options.copies),
            "-o",
            f"sides={options.duplex}",
            "-o",
            f"media={options.media}",
        ]
        if options.orientation == "landscape":
            command.extend(["-o", "orientation-requested=4"])
        command.extend(["--", str(pdf)])
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
        if result.returncode:
            raise PrinterError(
                (result.stderr or result.stdout).strip() or "CUPS hat den Auftrag abgelehnt."
            )
        output = result.stdout.strip()
        match = _JOB_ID.search(output)
        return match.group(1) if match else output or "übermittelt"
