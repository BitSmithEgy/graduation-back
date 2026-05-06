from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List

from database import get_db
from models import User, Doctors, Clinic
from schemas import DoctorCreate, DoctorUpdate, DoctorOut
from utils import require_role, get_current_user

router = APIRouter(prefix="/doctors", tags=["doctors"])

@router.get("/", response_model=List[DoctorOut])
def get_doctors(db: Session = Depends(get_db)):
    """Retrieve all active doctors."""
    doctors = db.query(Doctors).filter(Doctors.deleted_at == None).all()
    return doctors

@router.get("/{id}", response_model=DoctorOut)
def get_doctor(id: str, db: Session = Depends(get_db)):
    """Retrieve a specific doctor by ID."""
    doctor = db.query(Doctors).filter(Doctors.id == id, Doctors.deleted_at == None).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@router.post("/", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(
    doctor_in: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic"))
):
    """Create a new doctor. Accessible only by clinics."""
    if not current_user.clinic:
        raise HTTPException(status_code=400, detail="User does not have an associated clinic")
        
    new_doctor = Doctors(
        full_name=doctor_in.full_name,
        clinic_id=current_user.clinic.id,
        specialization_id=doctor_in.specialization_id,
        language_spoken=doctor_in.language_spoken,
        bio_en=doctor_in.bio_en,
        bio_ar=doctor_in.bio_ar,
        consultation_price_egp=doctor_in.consultation_price_egp,
        years_of_experiance=doctor_in.years_of_experiance,
        license_number=doctor_in.license_number,
        is_active=doctor_in.is_active
    )
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return new_doctor

@router.put("/{id}", response_model=DoctorOut)
def update_doctor(
    id: str,
    doctor_in: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin"))
):
    """Update an existing doctor."""
    doctor = db.query(Doctors).filter(Doctors.id == id, Doctors.deleted_at == None).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    if current_user.role.value == "clinic":
        if not current_user.clinic or doctor.clinic_id != current_user.clinic.id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this doctor")

    update_data = doctor_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(doctor, key, value)

    db.commit()
    db.refresh(doctor)
    return doctor

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin"))
):
    """Soft delete a doctor."""
    doctor = db.query(Doctors).filter(Doctors.id == id, Doctors.deleted_at == None).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if current_user.role.value == "clinic":
        if not current_user.clinic or doctor.clinic_id != current_user.clinic.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this doctor")

    doctor.deleted_at = func.now()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
