"""Read bounded excerpts from local documents for a shared evaluation prompt."""
import csv
import io
from itertools import islice
from pathlib import Path
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

FORMATS = "txt md csv tsv json jsonl log py sql yaml yml pdf doc docx ppt pptx xls xlsx".split()


def extract(name, data):
    ext = Path(name).suffix.lower()[1:]
    if ext not in FORMATS or len(data) > 5_000_000:
        raise ValueError("Choose a supported file up to 5 MB.")
    source = io.BytesIO(data)
    if ext in {"docx", "pptx", "xlsx"}:
        with ZipFile(source) as archive:
            if sum(member.file_size for member in archive.infolist()) > 40_000_000:
                raise ValueError("Expanded document exceeds 40 MB.")
        source.seek(0)
    if ext == "pdf":
        from pypdf import PdfReader
        pages = PdfReader(source).pages
        lines = [f"Page {i}\n{text}" for i,page in enumerate(islice(pages,20),1)
                 if (text := (page.extract_text() or "").strip())]
    elif ext == "docx":
        from docx import Document
        doc = Document(source)
        lines = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            lines.extend(" | ".join(c.text for c in row.cells) for row in table.rows)
    elif ext == "pptx":
        from pptx import Presentation
        lines = []
        for i, slide in enumerate(Presentation(source).slides,1):
            for shape in slide.shapes:
                if shape.has_text_frame and shape.text.strip():
                    lines.append(f"Slide {i}: {shape.text}")
                elif shape.has_table:
                    lines.extend(" | ".join(c.text for c in row.cells) for row in shape.table.rows)
    elif ext in {"xls","xlsx"}:
        import pandas as pd
        with pd.ExcelFile(source) as workbook:
            lines = []
            for sheet in workbook.sheet_names[:8]:
                frame = workbook.parse(sheet, header=None, nrows=100)
                lines.extend([f"Sheet: {sheet}",frame.to_csv(index=False,header=False)])
    elif ext in {"doc","ppt"}:
        tool = "antiword" if ext == "doc" else "catppt"
        if not shutil.which(tool):
            raise ValueError(f"Legacy .{ext} needs {tool}. You can also save as .{ext}x and upload again.")
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory)/("attachment."+ext)
            file.write_bytes(data)
            output = subprocess.run([tool,str(file)], capture_output=True,check=True,timeout=15)
            lines = output.stdout.decode("utf-8",errors="replace").splitlines()
    else:
        text = data.decode("utf-8-sig")
        if ext in {"csv","tsv"}:
            rows = csv.reader(io.StringIO(text), delimiter="," if ext=="csv" else "\t")
            lines = [" | ".join(row) for row in islice(rows,101)]
        else:
            lines = [text]
    content = "\n".join(lines).strip()
    if not content:
        raise ValueError("No readable text found. For scanned documents, apply OCR first.")
    return content[:6000]
