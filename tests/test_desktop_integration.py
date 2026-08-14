from pathlib import Path


def test_application_launcher_does_not_claim_document_associations():
    project_root = Path(__file__).parents[1]
    desktop_file = project_root / "resources/org.printqueue.PrintQueue.desktop"
    contents = desktop_file.read_text(encoding="utf-8")
    assert "MimeType=" not in contents


def test_dolphin_service_menu_contains_supported_mime_types():
    project_root = Path(__file__).parents[1]
    service_menu = project_root / "resources/dolphin/printqueue-servicemenu.desktop"
    contents = service_menu.read_text(encoding="utf-8")
    assert "MimeType=" in contents
    assert "application/vnd.oasis.opendocument.text" in contents
    assert "text/plain" in contents
