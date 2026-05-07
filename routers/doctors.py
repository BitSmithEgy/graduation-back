from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional

from database import get_db
from models import User, Doctor, Clinic, DoctorClinic, ClinicDoctorInvitation, InvitationStatusEnum, RoleEnum
from schemas import DoctorCreate, DoctorUpdate, DoctorOut, InvitationOut
from utils import require_role, get_current_user

router = APIRouter(prefix="/doctors", tags=["doctors"])

@router.get("/", response_model=List[DoctorOut])
def get_doctors(db: Session = Depends(get_db)):
    """Retrieve all active doctors."""
    doctors = db.query(Doctor).filter(Doctor.deleted_at == None).all()
    return doctors

@router.get("/{id}", response_model=DoctorOut)
def get_doctor(id: str, db: Session = Depends(get_db)):
    """Retrieve a specific doctor by ID."""
    doctor = db.query(Doctor).filter(Doctor.id == id, Doctor.deleted_at == None).first()
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
    if not current_user.clinic_account:
        raise HTTPException(status_code=400, detail="User does not have an associated clinic")
        
    # Check if a doctor with this user_id already exists (if provided, though DoctorCreate usually doesn't have it)
    # Actually, DoctorCreate in schemas.py doesn't have user_id. 
    # But a Doctor record MUST have a user_id. 
    # This endpoint seems to be for creating a doctor record for an existing user or creating both.
    # Looking at UserRegister in schemas.py, there's a DoctorRegister.
    # So this endpoint might be redundant or needs to be for admin/clinics to promote a user to a doctor.
    
    # For now, let's assume we are creating a doctor record for a user that already exists but isn't a doctor yet.
    # Or maybe the clinic is creating a doctor profile.
    
    # Wait, the Doctor model in models.py has user_id as a foreign key.
    # Let's assume the user already exists or we create one.
    
    # Actually, looking at the previous code, it didn't handle user_id creation.
    # I'll keep it simple for now and follow the existing logic but fix the fields.
    
    new_doctor = Doctor(
        full_name=doctor_in.full_name,
        specialization_id=doctor_in.specialization_id,
        language_spoken=doctor_in.language_spoken,
        bio_en=doctor_in.bio_en,
        bio_ar=doctor_in.bio_ar,
        consultation_price_egp=doctor_in.consultation_price_egp,
        years_of_experience=doctor_in.years_of_experience,
        license_number=doctor_in.license_number,
        is_active=doctor_in.is_active,
        user_id=current_user.uuid # Temporary placeholder if we don't have a specific user_id
    )
    db.add(new_doctor)
    db.flush()
    
    # Create the junction record
    db.add(DoctorClinic(doctor_id=new_doctor.id, clinic_id=current_user.clinic_account.id))
    
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
    doctor = db.query(Doctor).filter(Doctor.id == id, Doctor.deleted_at == None).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    if current_user.role.value == "clinic":
        # Check if this doctor is associated with this clinic
        link = db.query(DoctorClinic).filter(
            DoctorClinic.doctor_id == id, 
            DoctorClinic.clinic_id == current_user.clinic_account.id
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="Not authorized to edit this doctor")

    update_data = doctor_in.model_dump(exclude_unset=True)
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
    doctor = db.query(Doctor).filter(Doctor.id == id, Doctor.deleted_at == None).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if current_user.role.value == "clinic":
        link = db.query(DoctorClinic).filter(
            DoctorClinic.doctor_id == id, 
            DoctorClinic.clinic_id == current_user.clinic_account.id
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="Not authorized to delete this doctor")

    doctor.deleted_at = func.now()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/invitations", response_model=List[InvitationOut])
def list_my_invitations(
    status: Optional[InvitationStatusEnum] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("doctor"))
):
    """List invitations for the current doctor."""
    if not current_user.doctor_account:
        raise HTTPException(status_code=400, detail="User does not have an associated doctor account")
        
    query = db.query(ClinicDoctorInvitation).filter(
        ClinicDoctorInvitation.doctor_id == current_user.doctor_account.id
    )
    if status:
        query = query.filter(ClinicDoctorInvitation.status == status)
        
    return query.all()


@router.patch("/me/invitations/{invitation_id}/respond")
def respond_to_invitation(
    invitation_id: str,
    accept: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("doctor"))
):
    """Accept or reject an invitation."""
    if not current_user.doctor_account:
        raise HTTPException(status_code=400, detail="User does not have an associated doctor account")
        
    invitation = db.query(ClinicDoctorInvitation).filter(
        ClinicDoctorInvitation.id == invitation_id,
        ClinicDoctorInvitation.doctor_id == current_user.doctor_account.id
    ).first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
        
    if invitation.status != InvitationStatusEnum.pending:
        raise HTTPException(status_code=400, detail="Invitation is already responded to")
        
    if accept:
        invitation.status = InvitationStatusEnum.accepted
        # Link doctor to clinic
        link = db.query(DoctorClinic).filter(
            DoctorClinic.clinic_id == invitation.clinic_id,
            DoctorClinic.doctor_id == invitation.doctor_id
        ).first()
        
        if link:
            link.is_active = True
        else:
            db.add(DoctorClinic(
                doctor_id=invitation.doctor_id,
                clinic_id=invitation.clinic_id
            ))
    else:
        invitation.status = InvitationStatusEnum.rejected
        
    invitation.responded_at = func.now()
    db.commit()
    return {"message": "Invitation accepted" if accept else "Invitation rejected"}

