from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List

from database import get_db
from models import User, Specializations
from schemas import SpecializationCreate, SpecializationUpdate, SpecializationOut
from utils import require_admin

router = APIRouter(prefix="/specializations", tags=["specializations"])

@router.get("/", response_model=List[SpecializationOut])
def get_specializations(db: Session = Depends(get_db)):
    """Retrieve all active specializations (public)."""
    specializations = db.query(Specializations).filter(Specializations.deleted_at == None).all()
    return specializations

@router.get("/{id}", response_model=SpecializationOut)
def get_specialization(id: str, db: Session = Depends(get_db)):
    """Retrieve a specific specialization by ID (public)."""
    specialization = db.query(Specializations).filter(Specializations.id == id, Specializations.deleted_at == None).first()
    if not specialization:
        raise HTTPException(status_code=404, detail="Specialization not found")
    return specialization

@router.post("/", response_model=SpecializationOut, status_code=status.HTTP_201_CREATED)
def create_specialization(
    spec_in: SpecializationCreate, 
    db: Session = Depends(get_db), 
    admin: User = Depends(require_admin)
):
    """Create a new specialization (admin only)."""
    new_spec = Specializations(
        name_en=spec_in.name_en,
        name_ar=spec_in.name_ar,
        description_en=spec_in.description_en,
        description_ar=spec_in.description_ar
    )
    db.add(new_spec)
    db.commit()
    db.refresh(new_spec)
    return new_spec

@router.put("/{id}", response_model=SpecializationOut)
def update_specialization(
    id: str,
    spec_in: SpecializationUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Update an existing specialization (admin only)."""
    specialization = db.query(Specializations).filter(Specializations.id == id, Specializations.deleted_at == None).first()
    if not specialization:
        raise HTTPException(status_code=404, detail="Specialization not found")

    update_data = spec_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(specialization, key, value)

    db.commit()
    db.refresh(specialization)
    return specialization

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_specialization(
    id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Soft delete a specialization (admin only)."""
    specialization = db.query(Specializations).filter(Specializations.id == id, Specializations.deleted_at == None).first()
    if not specialization:
        raise HTTPException(status_code=404, detail="Specialization not found")

    specialization.deleted_at = func.now()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)