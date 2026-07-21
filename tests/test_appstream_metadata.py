from pathlib import Path
from xml.etree import ElementTree


def test_appstream_metadata_matches_desktop_entry_and_repository():
    project_root = Path(__file__).parents[1]
    metadata = project_root / "resources/org.printqueue.PrintQueue.metainfo.xml"
    root = ElementTree.parse(metadata).getroot()

    assert root.attrib["type"] == "desktop-application"
    assert root.findtext("id") == "org.printqueue.PrintQueue"
    assert root.findtext("launchable") == "org.printqueue.PrintQueue.desktop"
    assert root.findtext("url[@type='homepage']") == "https://github.com/geri777/print-queue/"

    screenshot = root.find("screenshots/screenshot/image")
    assert screenshot is not None
    assert screenshot.attrib == {"type": "source", "width": "1078", "height": "738"}
    assert screenshot.text == (
        "https://raw.githubusercontent.com/geri777/print-queue/main/resources/screenshot.png"
    )
