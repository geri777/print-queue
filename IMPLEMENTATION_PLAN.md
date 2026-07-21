# Implementation plan

## Phase 1 — Project foundation

- [x] Create the Python project and `pyproject.toml`
- [x] Define domain models for files, printers, and print options
- [x] Validate supported formats and collect file metadata

## Phase 2 — User interface

- [x] Implement the PySide6 main window and file table
- [x] Add a file dialog, drag and drop, removal, and reordering
- [x] Provide printer, copy, duplex, paper, and orientation controls
- [x] Read printer capabilities dynamically through CUPS

## Phase 3 — Print pipeline

- [x] Revalidate source files immediately before printing
- [x] Convert office documents to PDF with LibreOffice Headless
- [x] Convert images, including multi-page TIFF files, to PDF
- [x] Merge PDFs in list order
- [x] Submit one CUPS job and clean up temporary files
- [x] Display progress, cancellation, and errors in the user interface

## Phase 4 — KDE integration

- [x] Accept multiple files from the command line
- [x] Forward files to the running single instance
- [x] Provide an application launcher and Dolphin service menu
- [x] Provide a Nautilus extension for GNOME Files

## Phase 5 — Quality and distribution

- [x] Add unit tests for validation, PDF processing, the pipeline, and CUPS
- [x] Add Ruff, syntax, and CLI checks
- [x] Document the Nuitka/PySide6 deployment process
- [x] Provide scripts and metadata for Debian packaging
- [x] Split the main, Dolphin, and Nautilus integrations into separate Debian packages
- [ ] Run integration tests on KDE with LibreOffice, CUPS, and a real printer
- [ ] Add AppImage distribution after stabilizing the Debian package
