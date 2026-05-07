from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
import datetime

from database import get_db
from models import User, Doctor, DoctorAvailability
from schemas import AvailabilityCreate, AvailabilityUpdate, AvailabilityOut
from utils import require_role, get_current_user

router = APIRouter(prefix="/doctors/{doctor_id}/availability", tags=["availability"])

@router.get("/", response_model=List[AvailabilityOut])
def list_availability(
    doctor_id: str,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all availability rules for a doctor."""
    query = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor_id
    )
    if is_active is not None:
        query = query.filter(DoctorAvailability.is_active == is_active)
    
    return query.all()

@router.post("/", response_model=AvailabilityOut, status_code=status.HTTP_201_CREATED)
def create_availability(
    doctor_id: str,
    availability_in: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin", "doctor"))
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.deleted_at == None).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    print("current_user.uuid",current_user.uuid)
    print("doctor.user_id",doctor.user_id)
    if current_user.role.value == "doctor" and current_user.uuid != doctor.user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to create availability rule for this doctor")
    if availability_in.end_time <= availability_in.start_time:
        raise HTTPException(status_code=400, detail="end_time must be greater than start_time")
        
    # Check if this clinic is allowed to manage this doctor's availability
    # (Removed doctor.clinic_id check as it's many-to-many now)

    duplicate = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.day_of_week == availability_in.day_of_week,
        DoctorAvailability.start_time == availability_in.start_time,
    ).first()
    
    if duplicate:
        raise HTTPException(status_code=400, detail="Rule already exists for this day/time")

    new_rule = DoctorAvailability(
        doctor_id=doctor_id,
        **availability_in.model_dump()
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@router.patch("/{avail_id}", response_model=AvailabilityOut)
def update_availability(
    doctor_id: str,
    avail_id: str,
    availability_in: AvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin"))
):
    """Update an availability rule."""
    rule = db.query(DoctorAvailability).filter(
        DoctorAvailability.id == avail_id,
        DoctorAvailability.doctor_id == doctor_id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Availability rule not found")
        
    update_data = availability_in.model_dump(exclude_unset=True)
    if "start_time" in update_data or "end_time" in update_data:
        st = update_data.get("start_time", rule.start_time)
        et = update_data.get("end_time", rule.end_time)
        if et <= st:
             raise HTTPException(status_code=400, detail="end_time must be greater than start_time")

    for key, value in update_data.items():
        setattr(rule, key, value)
        
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/{avail_id}", status_code=200)
def delete_availability(
    doctor_id: str,
    avail_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin"))
):
    """Delete an availability rule."""
    rule = db.query(DoctorAvailability).filter(
        DoctorAvailability.id == avail_id,
        DoctorAvailability.doctor_id == doctor_id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Availability rule not found")
        
    db.delete(rule) # Availability rules can be hard deleted or we can add deleted_at to DoctorAvailability model
    db.commit()
    return {"message": "Availability rule deleted"}

