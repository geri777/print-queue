from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

from printqueue.domain import FileKind, QueueItem


class ConversionError(RuntimeError):
    pass


class ConversionService:
    def __init__(self, timeout_seconds: int = 180) -> None:
        self.timeout_seconds = timeout_seconds

    def convert(self, item: QueueItem, output_dir: Path) -> Path:
        self._validate_source(item)
        if item.kind is FileKind.PDF:
            return item.path
        if item.kind is FileKind.OFFICE:
            return self._convert_office(item.path, output_dir)
        return self._convert_image(item.path, output_dir)

    @staticmethod
    def _validate_source(item: QueueItem) -> None:
        if not item.path.is_file():
            raise ConversionError(f"Quelldatei ist nicht mehr vorhanden: {item.path}")

    def _convert_office(self, source: Path, output_dir: Path) -> Path:
        executable = shutil.which("libreoffice") or shutil.which("soffice")
        if not executable:
            raise ConversionError("LibreOffice ist nicht installiert oder nicht im PATH.")

        profile_dir = output_dir / "libreoffice-profile"
        profile_dir.mkdir()
        profile_uri = f"file://{quote(str(profile_dir.resolve()))}"
        command = [
            executable,
            f"-env:UserInstallation={profile_uri}",
            "--headless",
            "--nologo",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(source),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ConversionError(
                f"Zeitüberschreitung bei der Konvertierung von {source.name}"
            ) from exc

        target = output_dir / f"{source.stem}.pdf"
        if result.returncode or not target.is_file():
            details = (result.stderr or result.stdout).strip()
            raise ConversionError(
                details or f"LibreOffice konnte {source.name} nicht konvertieren."
            )
        return target

    @staticmethod
    def _convert_image(source: Path, output_dir: Path) -> Path:
        try:
            from PIL import Image, ImageSequence

            with Image.open(source) as image:
                pages = [
                    ConversionService._flatten_image(frame.copy())
                    for frame in ImageSequence.Iterator(image)
                ]
                if not pages:
                    raise ConversionError(f"Bild enthält keine Seiten: {source.name}")
                target = output_dir / f"{source.stem}.pdf"
                pages[0].save(target, "PDF", resolution=150, save_all=True, append_images=pages[1:])
                for page in pages:
                    page.close()
                return target
        except ConversionError:
            raise
        except Exception as exc:
            raise ConversionError(
                f"Bild konnte nicht konvertiert werden: {source.name}: {exc}"
            ) from exc

    @staticmethod
    def _flatten_image(image):
        from PIL import Image

        if image.mode == "RGB":
            return image
        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            rgba.close()
            image.close()
            return background
        converted = image.convert("RGB")
        image.close()
        return converted
