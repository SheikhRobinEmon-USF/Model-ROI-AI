import io
import json
import pytest
from docx import Document
from openpyxl import Workbook
from pptx import Presentation
from pypdf import PdfWriter
from app.datasets.attachments import extract
from app.datasets.analytical import analytical_cases
from app.graders.exact import grade

def test_analytical_keys():
    cases = analytical_cases()
    assert len(cases)==6 and len({c.task_type for c in cases})==3
    for case in cases:
        assert grade(case,json.dumps(case.expected))['passed']
        assert not grade(case,'{}')['passed']

def test_office_documents():
    doc=Document()
    doc.add_paragraph("Target: 72")
    deck=Presentation()
    deck.slides.add_slide(deck.slide_layouts[0]).shapes.title.text="Target: 72"
    book=Workbook()
    book.active.append(["Target: 72"])
    for suffix, obj in [('docx',doc),('pptx',deck),('xlsx',book)]:
        stream=io.BytesIO()
        obj.save(stream)
        assert "Target: 72" in extract("input."+suffix,stream.getvalue())

def test_csv_and_scanned_pdf():
    assert extract("case.csv",b'item,cost\n"tea, green",3')=="item | cost\ntea, green | 3"
    stream=io.BytesIO()
    writer=PdfWriter()
    writer.add_blank_page(width=200,height=200)
    writer.write(stream)
    with pytest.raises(ValueError,match="OCR"):
        extract("scan.pdf",stream.getvalue())
