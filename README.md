# PrintQueue für Linux

PrintQueue ist eine Desktop-Anwendung für KDE/Kubuntu, mit der sich mehrere Dokumente
sammeln, sortieren und als ein gemeinsamer CUPS-Druckauftrag ausgeben lassen. Sie ist als
Linux-Alternative zu Print Conductor konzipiert.

Dateien werden beim Hinzufügen nicht konvertiert. Die Konvertierung beginnt erst mit dem
Druckauftrag, damit die Bedienoberfläche unmittelbar reagiert.

## Funktionen

- Dateien per Drag & Drop oder Dateidialog hinzufügen
- mehrere Dateien über Kommandozeile und Dolphin-Kontextmenü übernehmen
- Reihenfolge ändern sowie einzelne oder alle Einträge entfernen
- Drucker, Kopien, Duplex, Papierformat und Ausrichtung auswählen
- Druckerfähigkeiten dynamisch über CUPS ermitteln
- Office-Dokumente über LibreOffice Headless in PDF konvertieren
- Bilder einschließlich mehrseitiger TIFF-Dateien in PDF konvertieren
- alle Dokumente in Listenreihenfolge zu einem Druckauftrag zusammenführen
- Fortschrittsanzeige, Abbruch und verständliche Fehlermeldungen
- neue Dateien an eine bereits laufende PrintQueue-Instanz übergeben

## Unterstützte Formate

| Kategorie | Formate |
|---|---|
| Dokumente | PDF |
| Microsoft Office | DOC, DOCX, XLS, XLSX, PPT, PPTX |
| OpenDocument | ODT, ODS, ODP |
| Bilder | PNG, JPG, JPEG, TIFF, BMP, WebP |

## Voraussetzungen

- Kubuntu oder eine vergleichbare Linux-Distribution mit KDE
- Python 3.10 oder neuer für Entwicklung und Quellinstallation
- CUPS-Clientprogramme `lp`, `lpstat` und `lpoptions`
- LibreOffice nur für Office- und OpenDocument-Dateien

Unter Ubuntu/Kubuntu lassen sich fehlende Laufzeitkomponenten gezielt installieren:

```bash
command -v lp >/dev/null || sudo apt install cups-client
command -v libreoffice >/dev/null || command -v soffice >/dev/null || sudo apt install libreoffice
```

Eine vorhandene LibreOffice-Installation wird dabei nicht erneut installiert. Auch eine
Installation außerhalb von APT wird berücksichtigt, sofern `libreoffice` oder `soffice`
über `PATH` erreichbar ist.

## Installation aus einem Debian-Paket

Ein veröffentlichtes Paket wird einschließlich seiner erforderlichen Abhängigkeiten mit
APT installiert:

```bash
sudo apt install ./printqueue_0.1.0_amd64.deb
```

LibreOffice ist im Paket bewusst nur als `Suggests` eingetragen. Ohne LibreOffice können
PDFs und Bilder weiterhin gedruckt werden; bei einer Office-Datei weist PrintQueue auf
die fehlende Komponente hin.

Deinstallation:

```bash
sudo apt remove printqueue
```

## Installation aus dem Quellcode

Repository klonen und eine isolierte Python-Umgebung erstellen:

```bash
git clone https://github.com/OWNER/printqueue.git
cd printqueue
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/printqueue
```

`OWNER` muss durch den tatsächlichen GitHub-Benutzer oder die Organisation ersetzt
werden.

## Bedienung

Die Anwendung kann ohne Parameter oder direkt mit mehreren Dateien gestartet werden:

```bash
printqueue
printqueue angebot.docx anhang.pdf scan.png
```

Weitere Aufrufe übergeben ihre Dateien an das bereits geöffnete Fenster. Nach dem
Drucken fragt PrintQueue, ob die Einträge aus der Liste entfernt werden sollen.

### Temporäre Dateien

Konvertierte Dateien liegen ausschließlich während der Druckvorbereitung in einem
geschützten Unterverzeichnis des System-Temp-Verzeichnisses, unter Linux normalerweise
unter `/tmp/printqueue-*`. Sie werden nach Übergabe an CUPS sowie bei Fehler oder Abbruch
automatisch entfernt.

## Dolphin-Integration bei einer Quellinstallation

Die Dateien für das Anwendungsmenü und Dolphin können benutzerspezifisch installiert
werden:

```bash
install -Dm644 resources/org.printqueue.PrintQueue.desktop \
  ~/.local/share/applications/org.printqueue.PrintQueue.desktop
install -Dm755 resources/dolphin/printqueue-servicemenu.desktop \
  ~/.local/share/kio/servicemenus/printqueue-servicemenu.desktop
```

Danach steht für unterstützte Dateien die Aktion **Zu PrintQueue hinzufügen** bereit.
Falls Dolphin bereits geöffnet war, muss es gegebenenfalls neu gestartet werden. Das
Debian-Paket installiert diese Integration systemweit.

## Entwicklung

Entwicklungsabhängigkeiten installieren:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
```

Tests und statische Prüfung ausführen:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Projektstruktur:

```text
src/printqueue/        Anwendung und Benutzeroberfläche
src/printqueue/services/ Konvertierungs- und Druckdienste
tests/                 automatisierte Tests
resources/             Desktop- und Dolphin-Integration
packaging/             Debian-Paketierung
```

## Eigenständiges Linux-Binary bauen

Qt stellt mit `pyside6-deploy` einen Nuitka-basierten Deployment-Weg bereit. Für einen
Build unter Ubuntu/Kubuntu werden zusätzlich Compiler- und Paketwerkzeuge benötigt:

```bash
sudo apt install python3-venv build-essential dpkg-dev libxkbcommon0
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/pyside6-deploy src/printqueue/main.py \
  --name PrintQueue \
  --mode onefile
```

Das Binary wird derzeit als `src/printqueue/deployment/main.bin` erzeugt. Es enthält
Python, PySide6/Qt und die benötigten Python-Bibliotheken. CUPS und LibreOffice bleiben
Systemkomponenten.

## Debian-Paket bauen

Aus dem erzeugten Binary erstellt das mitgelieferte Skript ein installierbares `.deb`:

```bash
packaging/build-deb.sh src/printqueue/deployment/main.bin 0.1.0
```

Das Ergebnis liegt abhängig von der Architektur beispielsweise hier:

```text
dist/printqueue_0.1.0_amd64.deb
```

Paket kontrollieren und installieren:

```bash
dpkg-deb --info dist/printqueue_0.1.0_amd64.deb
dpkg-deb --contents dist/printqueue_0.1.0_amd64.deb
sudo apt install ./dist/printqueue_0.1.0_amd64.deb
```

## `.deb` veröffentlichen

Ja, PrintQueue kann als `.deb` veröffentlicht werden. Vor einem GitHub-Release sollten
folgende Schritte abgeschlossen werden:

1. Versionsnummer in `pyproject.toml` und `src/printqueue/__init__.py` aktualisieren.
2. Tests und Ruff-Prüfungen erfolgreich ausführen.
3. Das Binary auf der ältesten unterstützten Ubuntu-/Kubuntu-Version bauen. Ein dort
   gebautes Binary ist wegen der glibc-Kompatibilität meist auch auf neueren Versionen
   lauffähig; umgekehrt gilt das nicht zuverlässig.
4. Das `.deb` mit derselben Versionsnummer erzeugen.
5. Installation, Programmstart, LibreOffice-Konvertierung, CUPS-Druck und Deinstallation
   in einer sauberen VM testen.
6. Prüfsumme erzeugen:

   ```bash
   sha256sum dist/printqueue_0.1.0_amd64.deb \
     > dist/printqueue_0.1.0_amd64.deb.sha256
   ```

7. Git-Tag wie `v0.1.0` erstellen und `.deb` sowie `.sha256` an den GitHub-Release
   anhängen.

Für verschiedene Ubuntu-Versionen oder CPU-Architekturen sollten getrennte Pakete in
reproduzierbaren CI-Umgebungen gebaut und getestet werden.

## Lizenz

Das Projekt ist derzeit als **GPL-3.0-or-later** deklariert. Vor einem öffentlichen
Release sollte zusätzlich eine vollständige `LICENSE`-Datei ins Repository aufgenommen
und die Lizenzierung aller mitgelieferten Komponenten geprüft werden.
