import pytest
from core.usecases import PDFProcessor, TXTProcessor, DOCXProcessor

def test_pdf_processor():
    processor = PDFProcessor()
    result = processor.extract_text(open("sample.pdf", "rb"))
    assert result == "Texto de PDF"

def test_txt_processor():
    processor = TXTProcessor()
    result = processor.extract_text(open("sample.txt", "rb"))
    assert result == "Contenido del archivo TXT"

def test_docx_processor():
    processor = DOCXProcessor()
    result = processor.extract_text(open("sample.docx", "rb"))
    assert result == "Contenido del archivo DOCX"