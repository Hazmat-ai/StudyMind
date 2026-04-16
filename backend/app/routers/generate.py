from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.generate import GenerateRequest, GenerateResponse
from ..services.ai import generate_study_set
from ..services.pdf import extract_text_from_pdf

router = APIRouter()

@router.post("", response_model=GenerateResponse)
async def generate_endpoint(request: GenerateRequest):
    try:
        result = await generate_study_set(request.content, request.options)
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.post("/extract-pdf")
async def extract_pdf_endpoint(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Must be a PDF file")
    try:
        text = await extract_text_from_pdf(file)
        return {"content": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
