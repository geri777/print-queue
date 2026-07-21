from pypdf import PdfReader, PdfWriter

from printqueue.services.pdf_service import merge_pdfs


def _create_pdf(path, pages):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    with path.open("wb") as output:
        writer.write(output)


def test_merge_pdfs_preserves_order_and_page_count(tmp_path):
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    target = tmp_path / "merged.pdf"
    _create_pdf(first, 1)
    _create_pdf(second, 2)
    merge_pdfs([first, second], target)
    assert len(PdfReader(target).pages) == 3
