from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import date, datetime, time, timedelta

from database import get_db
from models import User, Doctor, DoctorAvailability, AppointmentSlot, SlotStatusEnum
from schemas import SlotCreate, SlotGenerateRequest, SlotStatusUpdate, SlotOut, SlotGenerationResponse
from utils import require_role, get_current_user

router = APIRouter(prefix="/appointment-slots", tags=["slots"])

@router.get("/", response_model=List[SlotOut])
def list_slots(
    doctor_id: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    slot_status: SlotStatusEnum = SlotStatusEnum.available,
    db: Session = Depends(get_db)
):
    """List slots for a doctor."""
    query = db.query(AppointmentSlot).filter(
        AppointmentSlot.doctor_id == doctor_id,
        AppointmentSlot.deleted_at == None,
        AppointmentSlot.slot_status == slot_status
    )
    
    if from_date:
        query = query.filter(AppointmentSlot.slot_date >= from_date)
    if to_date:
        query = query.filter(AppointmentSlot.slot_date <= to_date)
        
    return query.all()

@router.get("/{slot_id}", response_model=SlotOut)
def get_slot(
    slot_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single slot detail."""
    slot = db.query(AppointmentSlot).filter(
        AppointmentSlot.id == slot_id,
        AppointmentSlot.deleted_at == None
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot

@router.post("/generate", response_model=SlotGenerationResponse)
def generate_slots(
    payload: SlotGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin", "doctor"))
):
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id, Doctor.deleted_at == None).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if current_user.role.value == "doctor" and current_user.uuid != doctor.user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to create availability rule for this doctor")
    if payload.to_date < payload.from_date:
        raise HTTPException(status_code=400, detail="to_date must be >= from_date")
    if (payload.to_date - payload.from_date).days > 90:
        raise HTTPException(status_code=400, detail="Max date range is 90 days")

    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    # Permission check for clinics - can skip for now or implement junction check
    # if current_user.role.value == "clinic":
    #    ...

    rules = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == payload.doctor_id,
        DoctorAvailability.is_active == True,
        DoctorAvailability.deleted_at == None
    )
    if payload.clinic_id:
        rules = rules.filter(DoctorAvailability.clinic_id == payload.clinic_id)
    
    rules = rules.all()
    
    rules_by_day = {i: [] for i in range(7)}
    for r in rules:
        rules_by_day[r.day_of_week].append(r)

    generated = 0
    skipped = 0
    
    current_date = payload.from_date
    all_generated_slots = []
    while current_date <= payload.to_date:
        day_rules = rules_by_day[current_date.weekday()]
        for rule in day_rules:
            # use datetime.combine to add timedelta
            curr_time_dt = datetime.combine(current_date, rule.start_time)
            end_time_dt = datetime.combine(current_date, rule.end_time)
            
            while curr_time_dt + timedelta(minutes=rule.slot_duration_minutes) <= end_time_dt:
                slot_start = curr_time_dt.time()
                slot_end = (curr_time_dt + timedelta(minutes=rule.slot_duration_minutes)).time()
                
                # Check if slot already exists
                exists = db.query(AppointmentSlot).filter(
                    AppointmentSlot.doctor_id == payload.doctor_id,
                    AppointmentSlot.slot_date == current_date,
                    AppointmentSlot.slot_start_time == slot_start,
                    AppointmentSlot.deleted_at == None
                ).first()
                
                if not exists:
                    new_slot = AppointmentSlot(
                        doctor_id=payload.doctor_id,
                        clinic_id=rule.clinic_id,
                        availability_id=rule.id,
                        slot_date=current_date,
                        slot_start_time=slot_start,
                        slot_end_time=slot_end,
                        slot_status=SlotStatusEnum.available
                    )
                    db.add(new_slot)
                    all_generated_slots.append(new_slot)
                    generated += 1
                else:
                    skipped += 1
                    
                curr_time_dt += timedelta(minutes=rule.slot_duration_minutes)
                
        current_date += timedelta(days=1)
        
    db.commit()
    return {
        "generated": generated, 
        "skipped": skipped,
        "slots": all_generated_slots
    }

@router.post("/", response_model=SlotOut, status_code=status.HTTP_201_CREATED)
def create_slot(
    slot_in: SlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin"))
):
    """Create a single slot manually."""
    rule = db.query(DoctorAvailability).filter(
        DoctorAvailability.id == slot_in.availability_id,
        DoctorAvailability.deleted_at == None
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Availability rule not found")
            
    if slot_in.slot_end_time <= slot_in.slot_start_time:
        raise HTTPException(status_code=400, detail="slot_end_time must be > slot_start_time")

    # check duplicates
    exists = db.query(AppointmentSlot).filter(
        AppointmentSlot.doctor_id == rule.doctor_id,
        AppointmentSlot.slot_date == slot_in.slot_date,
        AppointmentSlot.slot_start_time == slot_in.slot_start_time,
        AppointmentSlot.deleted_at == None
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Slot already exists for this date and time")

    new_slot = AppointmentSlot(
        doctor_id=rule.doctor_id,
        clinic_id=rule.clinic_id,
        slot_status=SlotStatusEnum.available,
        **slot_in.model_dump()
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    return new_slot

@router.patch("/{slot_id}", response_model=SlotOut)
def update_slot(
    slot_id: str,
    slot_in: SlotStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "doctor", "admin"))
):
    """Update status."""
    slot = db.query(AppointmentSlot).filter(
        AppointmentSlot.id == slot_id,
        AppointmentSlot.deleted_at == None
    ).first()
    
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
            
    if slot.slot_status == SlotStatusEnum.booked and slot_in.slot_status == SlotStatusEnum.available:
        raise HTTPException(status_code=409, detail="Cannot change a booked slot to available")

    # The spec allows update to 'booked', 'blocked', 'cancelled' etc.
    slot.slot_status = slot_in.slot_status
    db.commit()
    db.refresh(slot)
    return slot

@router.delete("/{slot_id}", status_code=200)
def delete_slot(
    slot_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clinic", "doctor"))
):
    """Hard delete slot."""
    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
        
    if slot.slot_status == SlotStatusEnum.booked:
        raise HTTPException(status_code=400, detail="Cannot delete a booked slot")
        
    db.delete(slot)
    db.commit()
    return {"message": "Slot deleted"}
