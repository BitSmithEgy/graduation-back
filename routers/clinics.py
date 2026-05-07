from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional

from database import get_db
from models import User, Clinic, DoctorClinic, Doctor, ClinicDoctorInvitation, Specialization, InvitationStatusEnum, RoleEnum
from schemas import ClinicOut, DoctorOut, InvitationOut, InvitationCreate
from utils import require_role, get_current_user

router = APIRouter(prefix="/clinics", tags=["clinics"])

@router.get("/", response_model=List[ClinicOut])
def list_clinics(db: Session = Depends(get_db)):
    """List all clinics."""
    return db.query(Clinic).filter(Clinic.deleted_at == None).all()
@router.get("/search/doctors", response_model=List[DoctorOut])
def search_doctors(
    specialization_id: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    print("specialization_id =", specialization_id)

    query = db.query(Doctor).filter(Doctor.deleted_at == None)

    if specialization_id:
        query = query.filter(
            Doctor.specialization_id == specialization_id
        )

    return query.all()
@router.get("/{clinic_id}", response_model=ClinicOut)
def get_clinic(clinic_id: str, db: Session = Depends(get_db)):
    """Get clinic details."""
    clinic = db.query(Clinic).filter(Clinic.id == clinic_id, Clinic.deleted_at == None).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic

@router.get("/{clinic_id}/doctors", response_model=List[DoctorOut])
def get_clinic_doctors(clinic_id: str, db: Session = Depends(get_db)):
    """List doctors working at this clinic."""
    doctors = db.query(Doctor).join(DoctorClinic).filter(
        DoctorClinic.clinic_id == clinic_id,
        DoctorClinic.is_active == True,
        Doctor.deleted_at == None
    ).all()
    return doctors

@router.post("/{clinic_id}/doctors/{doctor_id}", status_code=201)
def link_doctor_to_clinic(
    clinic_id: str,
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin"))
):
    """Link a doctor to a clinic."""
    # Permission check: current_user must be the owner of the clinic OR an admin
    if current_user.role.value == "clinic" and current_user.clinic_account.id != clinic_id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this clinic")
        
    # Check if link already exists
    exists = db.query(DoctorClinic).filter(
        DoctorClinic.clinic_id == clinic_id,
        DoctorClinic.doctor_id == doctor_id
    ).first()
    
    if exists:
        if exists.is_active:
            raise HTTPException(status_code=400, detail="Doctor is already linked to this clinic")
        else:
            exists.is_active = True
            db.commit()
            return {"message": "Doctor re-linked to clinic"}

    new_link = DoctorClinic(clinic_id=clinic_id, doctor_id=doctor_id)
    db.add(new_link)
    db.commit()
    return {"message": "Doctor linked to clinic successfully"}

@router.delete("/{clinic_id}/doctors/{doctor_id}")
def unlink_doctor_from_clinic(
    clinic_id: str,
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin"))
):
    """Unlink a doctor from a clinic."""
    if current_user.role.value == "clinic" and current_user.clinic_account.id != clinic_id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this clinic")
        
    link = db.query(DoctorClinic).filter(
        DoctorClinic.clinic_id == clinic_id,
        DoctorClinic.doctor_id == doctor_id
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
        
    link.is_active = False
    link.left_at = func.now()
    db.commit()
    return {"message": "Doctor unlinked from clinic"}






@router.post("/{clinic_id}/invitations", response_model=InvitationOut, status_code=201)
def send_invitation(
    clinic_id: str,
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "admin"))
):
    """Clinic sends an invitation to a doctor."""
    print("current_user.clinic_account.id = ", current_user.clinic_account.id)
    print("clinic_id = ", clinic_id)
    if current_user.role.value == "clinic" and (not current_user.clinic_account or current_user.clinic_account.id != clinic_id):
        raise HTTPException(status_code=403, detail="Not authorized to manage this clinic")
        
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id, Doctor.deleted_at == None).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    # Check if already linked
    linked = db.query(DoctorClinic).filter(
        DoctorClinic.clinic_id == clinic_id,
        DoctorClinic.doctor_id == payload.doctor_id,
        DoctorClinic.is_active == True
    ).first()
    if linked:
        raise HTTPException(status_code=400, detail="Doctor is already linked to this clinic")
        
    # Check if a pending invitation exists
    exists = db.query(ClinicDoctorInvitation).filter(
        ClinicDoctorInvitation.clinic_id == clinic_id,
        ClinicDoctorInvitation.doctor_id == payload.doctor_id,
        ClinicDoctorInvitation.status == InvitationStatusEnum.pending
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="A pending invitation already exists")
        
    invitation = ClinicDoctorInvitation(
        clinic_id=clinic_id,
        doctor_id=payload.doctor_id,
        message=payload.message
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation
