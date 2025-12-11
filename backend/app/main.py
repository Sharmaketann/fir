from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from pathlib import Path

app = FastAPI(title="FIR OCR Extraction API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
MODELS_DIR = Path("trained_models")
TRAINING_DIR = Path("training_data")

for dir in [UPLOAD_DIR, MODELS_DIR, TRAINING_DIR]:
    dir.mkdir(exist_ok=True)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import routes
from app.routes import upload, train

app.include_router(upload.router, prefix="/api", tags=["OCR"])
app.include_router(train.router, prefix="/api/train", tags=["Training"])