# medical_record_service.py
from sqlalchemy.orm import Session
from models import (
    MedicalRecord, User, UserProfile,
    Diagnostic, DiagnosticResult
)
from datetime import datetime
import uuid


def _build_patient_section(user: User, profile: UserProfile | None) -> dict:
    return {
        "name": user.full_name,
        "date_of_birth": str(profile.date_of_birth) if profile and profile.date_of_birth else None,
        "gender": profile.gender.value if profile and profile.gender else None,  # ✅
        "phone": user.phone,
    }


def _build_alerts_section(profile: UserProfile | None) -> dict:
    def split_or_empty(val):
        return [v.strip() for v in val.split(",")] if val else []

    return {
        "allergies": split_or_empty(profile.known_allergies if profile else None),
        "chronic_diseases": split_or_empty(profile.chronic_conditions if profile else None),
    }


def _build_diagnostics_section(db: Session, user_id: str) -> list:
    rows = (
        db.query(Diagnostic)
        .filter(Diagnostic.user_id == user_id)
        .order_by(Diagnostic.created_at.desc())
        .all()
    )

    entries = []
    for d in rows:
        result = d.result  
        entries.append({
            "date": str(d.created_at),
            "key_readings": {
                "glucose":        {"value": d.glucose,        "unit": "mg/dL"},
                "bmi":            {"value": d.bmi,            "unit": "kg/m²"},
                "blood_pressure": {"value": d.blood_pressure, "unit": "mmHg"},
                "skin_thickness": {"value": d.skin_thickness, "unit": "mm"},
                "insulin":        {"value": d.insulin,        "unit": "μU/mL"},
                "diabetes_pedigree_function": {"value": d.diabetes_pedigree_function, "unit": ""},
                "age":            {"value": d.age,            "unit": "years"},
                "pregnancies":    {"value": d.pregnancies,    "unit": ""},
            },
            "result": {
                "risk_level":       result.risk_level  if result else None,
                "confidence_score": result.confidence   if result else None,  
            },
        })
    return entries


def _build_visits_section(user: User) -> list:
    """Build from already-loaded relationships (bookings eager-loaded)."""
    visits = []
    for booking in (user.bookings or []):
        slot     = booking.slot
        clinic   = booking.clinic

        doctor_name = None
        specialty   = None
        if slot and slot.availability:
            doc = slot.availability.doctor
            if doc:
                doctor_name = doc.full_name
                if doc.specialization:
                    specialty = doc.specialization.name_en

        notes = []
        if booking.notes and booking.notes.notes:
            notes = [booking.notes.notes]

        visits.append({
            "date":    str(booking.created_at),
            "clinic":  {"name": clinic.name if clinic else None,
                        "address": clinic.address if clinic else None},
            "doctor":   doctor_name,
            "specialty": specialty,
            "status":   booking.booking_status.value if booking.booking_status else None,
            "notes":    notes,
        })
    return visits


def upsert_medical_record(db: Session, user_id: str) -> MedicalRecord:
    """
    Rebuild and save (insert or update) the medical record JSON for a user.
    Call this after every analysis run or xray upload.
    """
    user: User = db.query(User).filter(User.uuid == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    profile: UserProfile | None = user.profile

    record_json = {
        "record_id":    str(uuid.uuid4()),
        "generated_at": datetime.utcnow().isoformat(),

        "patient":        _build_patient_section(user, profile),
        "medical_alerts": _build_alerts_section(profile),


        "radiology":           [],
        "chat_consultations":  [],

        "diagnostics": _build_diagnostics_section(db, user_id),
        "visits":      _build_visits_section(user),
    }

    med_record: MedicalRecord | None = (
        db.query(MedicalRecord).filter(MedicalRecord.user_id == user_id).first()
    )

    if med_record is None:
        med_record = MedicalRecord(user_id=user_id, record=record_json)
        db.add(med_record)
    else:
        med_record.record = record_json

    db.commit()
    db.refresh(med_record)
    return med_record