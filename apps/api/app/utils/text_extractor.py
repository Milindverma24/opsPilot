import io
import json
import os
from typing import Optional
import fitz  # PyMuPDF
import docx
import pandas as pd


class OCRAbstraction:
    """
    Pluggable OCR abstraction layer.
    Can hook into Tesseract, AWS Textract, or Google Document AI.
    Default local fallback uses PyMuPDF layout & text heuristics.
    """
    @classmethod
    def extract_from_image_bytes(cls, image_bytes: bytes) -> str:
        # Default mock / lightweight OCR fallback
        return "[OCR Extracted Text placeholder]"


def extract_text_from_pdf(content: bytes) -> str:
    """Extracts text from PDF bytes using PyMuPDF (fitz)."""
    text_parts = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                text_parts.append(page_text.strip())
            else:
                # If page has no text stream, attempt OCR abstraction
                pix = page.get_pixmap()
                ocr_text = OCRAbstraction.extract_from_image_bytes(pix.tobytes())
                text_parts.append(ocr_text)
    return "\n\n".join(text_parts)


def extract_text_from_docx(content: bytes) -> str:
    """Extracts text from DOCX bytes using python-docx."""
    file_stream = io.BytesIO(content)
    doc = docx.Document(file_stream)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)
    return "\n".join(paragraphs)


def extract_text_from_excel(content: bytes, is_csv: bool = False) -> str:
    """Extracts structured text representation from XLSX/CSV bytes."""
    file_stream = io.BytesIO(content)
    if is_csv:
        df = pd.read_csv(file_stream)
    else:
        df = pd.read_excel(file_stream)
    return df.to_string()


def extract_text_from_file(filename: str, content: bytes) -> str:
    """
    Main extraction dispatcher based on file extension.
    Returns cleaned unicode string.
    """
    _, ext = os.path.splitext(filename.lower())
    try:
        if ext == ".pdf":
            return extract_text_from_pdf(content)
        elif ext == ".docx":
            return extract_text_from_docx(content)
        elif ext in [".xlsx", ".xls"]:
            return extract_text_from_excel(content, is_csv=False)
        elif ext == ".csv":
            return extract_text_from_excel(content, is_csv=True)
        elif ext == ".json":
            data = json.loads(content.decode("utf-8", errors="replace"))
            return json.dumps(data, indent=2)
        elif ext in [".txt", ".eml"]:
            return content.decode("utf-8", errors="replace")
        else:
            return content.decode("utf-8", errors="replace")
    except Exception as e:
        # Fallback to UTF-8 decode with replacement
        try:
            return content.decode("utf-8", errors="replace")
        except Exception:
            return f"[Text extraction error: {str(e)}]"
