from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import shutil
from pathlib import Path
import uuid
from app.services.extraction_service import FIRExtractionService
from app.services.ocr_service import OCRService

router = APIRouter()

extraction_service = FIRExtractionService()
ocr_service = OCRService()

@router.post("/upload")
async def upload_and_extract(file: UploadFile = File(...)):
    """Upload PDF and extract FIR data"""

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = Path("uploads") / f"{file_id}.pdf"

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text from PDF
        try:
            text_data = ocr_service.extract_text_from_pdf(str(file_path))
        except Exception as e:
            print(f"OCR failed: {e}")
            text_data = {}

        # Extract structured fields from first page
        if 1 in text_data and text_data[1]:
            extracted_data = extraction_service.extract_fields(text_data[1])
        else:
            extracted_data = {}

        return JSONResponse(content={
            "file_id": file_id,
            "filename": file.filename,
            "text_data": text_data,
            "extracted_fields": extracted_data
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/file/{file_id}")
async def get_file(file_id: str):
    """Get uploaded PDF file"""
    file_path = Path("uploads") / f"{file_id}.pdf"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type="application/pdf")
