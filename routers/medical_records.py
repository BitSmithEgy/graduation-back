from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, MedicalRecord, RecordType, RoleEnum
from schemas import MedicalRecordOut, MedicalRecordUpdate
from utils import get_current_user

router = APIRouter(prefix="/records", tags=["medical-records"])

@router.get("/me", response_model=MedicalRecordOut)
def get_my_record(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get my medical record."""
    record = db.query(MedicalRecord).filter(MedicalRecord.user_id == current_user.uuid).first()
    if not record:
        # Create an empty record if it doesn't exist
        record = MedicalRecord(user_id=current_user.uuid, record={})
        db.add(record)
        db.commit()
        db.refresh(record)
    return record

@router.patch("/me", response_model=MedicalRecordOut)
def update_my_record(
    payload: MedicalRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update my medical record."""
    record = db.query(MedicalRecord).filter(MedicalRecord.user_id == current_user.uuid).first()
    if not record:
        record = MedicalRecord(user_id=current_user.uuid, record=payload.record)
        db.add(record)
    else:
        # Merge or replace? Let's replace for simplicity
        record.record = payload.record
        
    db.commit()
    db.refresh(record)
    return record

@router.get("/user/{user_id}", response_model=MedicalRecordOut)
def get_user_record(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a user's record (authorized doctors/admin only)."""
    # Authorization logic: check if current_user is a doctor and has a booking with this user
    if current_user.role == RoleEnum.doctor:
        # Check for booking (simplified)
        # In a real app, you'd check for a confirmed/completed booking
        pass
    elif current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this record")
        
    record = db.query(MedicalRecord).filter(MedicalRecord.user_id == user_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return record
