from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import User
from utils import get_current_user
from typing import Dict
import os
import shutil
from datetime import datetime
import random
router = APIRouter(prefix="/xray", tags=["xray"])

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=Dict[str, str])
async def upload_xray(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"xray_{current_user.uuid}_{timestamp}.{file.filename.split('.')[-1]}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    disease_classes = ["normal", "pneumonia", "covid"]
    predicted_disease = random.choice(disease_classes)
    confidence_score = round(random.uniform(0.7, 0.99), 2)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"diagnosis": predicted_disease, "confidence": confidence_score}