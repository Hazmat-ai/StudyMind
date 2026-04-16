import fitz  # PyMuPDF
from fastapi import UploadFile

async def extract_text_from_pdf(file: UploadFile) -> str:
    try:
        content = await file.read()
        pdf_document = fitz.open(stream=content, filetype="pdf")
        
        text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
            
        pdf_document.close()
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {e}")
