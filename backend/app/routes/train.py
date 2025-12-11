from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
from app.services.training_service import TrainingService

router = APIRouter()

training_service = TrainingService()

class TrainingSample(BaseModel):
    file_id: str
    ocr_data: Dict[str, Any]
    corrected_data: Dict[str, Any]

@router.post("/sample")
async def save_training_sample(sample: TrainingSample):
    """Save a corrected extraction as training sample"""
    success = training_service.save_training_sample(
        sample.file_id,
        sample.ocr_data,
        sample.corrected_data
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save training sample")

    return JSONResponse(content={"message": "Training sample saved successfully"})

@router.get("/samples")
async def get_training_samples():
    """Get all training samples"""
    samples = training_service.get_training_samples()
    return JSONResponse(content={"samples": samples})

@router.post("/retrain")
async def retrain_model():
    """Retrain the extraction model"""
    result = training_service.retrain_model()
    return JSONResponse(content=result)