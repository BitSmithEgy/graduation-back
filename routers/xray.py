from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Radiology, RadiologyFinding
from schemas import RadiologyOut
from utils import get_current_user
from typing import Dict, List
import os
import shutil
from datetime import datetime
import random
from medical_record_service import upsert_medical_record 

router = APIRouter(prefix="/xray", tags=["xray"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=RadiologyOut)
async def upload_xray(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"xray_{current_user.uuid}_{timestamp}.{file.filename.split('.')[-1]}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    disease_classes = ["normal", "pneumonia", "covid"]
    predicted_disease = random.choice(disease_classes)
    confidence_score = round(random.uniform(0.7, 0.99), 2)

    # Save to DB
    radiology = Radiology(
        user_id=current_user.uuid,
        image_path=file_path,
        body_part="chest"
    )
    db.add(radiology)
    db.flush()
    
    finding = RadiologyFinding(
        radiology_id=radiology.id,
        finding_name=predicted_disease,
        confidence_score=confidence_score
    )
    db.add(finding)
    
    db.commit()
    db.refresh(radiology)
    
    upsert_medical_record(db, current_user.uuid) 
    return radiology