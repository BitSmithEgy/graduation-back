from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import date, datetime

from database import get_db
from models import User, Doctor, DoctorAvailability, AppointmentSlot, Booking, SlotStatusEnum, BookingStatusEnum, RoleEnum
from schemas import BookingCreate, BookingReschedule, BookingStatusUpdate, BookingOut
from utils import require_role, get_current_user

router = APIRouter(prefix="/bookings", tags=["bookings"])

def enrich_booking_for_output(booking: Booking) -> BookingOut:
    """Helper to ensure the booking object is ready for validation."""
    # The relationships in models.py should handle most of this now.
    return BookingOut.model_validate(booking)


@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atomic booking creation flow."""
    slot = db.query(AppointmentSlot).filter(
        AppointmentSlot.id == payload.slot_id,
        AppointmentSlot.deleted_at == None
    ).first()
    
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot.slot_status != SlotStatusEnum.available:
        raise HTTPException(status_code=409, detail="Slot is not available")
        
    doctor_id = slot.doctor_id
    
    # Check if user already has a pending/confirmed booking for this doctor on this day
    existing_booking = db.query(Booking).join(AppointmentSlot).filter(
        Booking.user_id == current_user.uuid,
        Booking.doctor_id == doctor_id,
        AppointmentSlot.slot_date == slot.slot_date,
        Booking.booking_status.in_([BookingStatusEnum.pending, BookingStatusEnum.confirmed]),
        Booking.deleted_at == None
    ).first()
    
    if existing_booking:
        raise HTTPException(status_code=409, detail="User already has a booking for this doctor on that date")
        
    new_booking = Booking(
        slot_id=slot.id,
        user_id=current_user.uuid,
        doctor_id=doctor_id,
        clinic_id=slot.clinic_id,
        booking_status=BookingStatusEnum.pending,
        booking_source_id=payload.booking_source_id
    )
    
    slot.slot_status = SlotStatusEnum.booked
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    return enrich_booking_for_output(new_booking)


@router.get("/me", response_model=List[BookingOut])
def get_my_bookings(
    booking_status: Optional[BookingStatusEnum] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    doctor_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get my bookings (User)."""
    query = db.query(Booking).filter(
        Booking.user_id == current_user.uuid,
        Booking.deleted_at == None
    )
    
    if booking_status:
        query = query.filter(Booking.booking_status == booking_status)
    if from_date:
        query = query.join(AppointmentSlot).filter(AppointmentSlot.slot_date >= from_date)
    if to_date:
        query = query.join(AppointmentSlot).filter(AppointmentSlot.slot_date <= to_date)
    if doctor_id:
        query = query.filter(Booking.doctor_id == doctor_id)
        
    bookings = query.all()
    return [enrich_booking_for_output(b) for b in bookings]


@router.get("/doctor/me", response_model=List[BookingOut])
def get_doctor_bookings(
    doctor_id: Optional[str] = None,
    booking_status: Optional[BookingStatusEnum] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "doctor"))
):
    """Get bookings for a clinic or doctor."""
    query = db.query(Booking).filter(Booking.deleted_at == None)
    
    if current_user.role == RoleEnum.clinic:
        if not current_user.clinic_account:
            raise HTTPException(status_code=403, detail="Clinic not found")
        query = query.filter(Booking.clinic_id == current_user.clinic_account.id)
    elif current_user.role == RoleEnum.doctor:
        if not current_user.doctor_account:
            raise HTTPException(status_code=403, detail="Doctor account not found")
        query = query.filter(Booking.doctor_id == current_user.doctor_account.id)
        
    if doctor_id:
        query = query.filter(Booking.doctor_id == doctor_id)
    if booking_status:
        query = query.filter(Booking.booking_status == booking_status)
    if from_date:
        query = query.join(AppointmentSlot).filter(AppointmentSlot.slot_date >= from_date)
    if to_date:
        query = query.join(AppointmentSlot).filter(AppointmentSlot.slot_date <= to_date)
        
    bookings = query.all()
    return [enrich_booking_for_output(b) for b in bookings]


@router.get("/", response_model=List[BookingOut])
def get_all_bookings(
    user_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
    clinic_id: Optional[str] = None,
    booking_status: Optional[BookingStatusEnum] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get all bookings (Admin)."""
    query = db.query(Booking).filter(Booking.deleted_at == None)
    
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    if clinic_id:
        query = query.filter(Booking.clinic_id == clinic_id)
    if doctor_id:
        query = query.filter(Booking.doctor_id == doctor_id)
    if booking_status:
        query = query.filter(Booking.booking_status == booking_status)
    if from_date:
        query = query.join(AppointmentSlot).filter(AppointmentSlot.slot_date >= from_date)
    if to_date:
        query = query.join(AppointmentSlot).filter(AppointmentSlot.slot_date <= to_date)
        
    bookings = query.all()
    return [enrich_booking_for_output(b) for b in bookings]


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full detail of a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.deleted_at == None).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if current_user.role == RoleEnum.user and booking.user_id != current_user.uuid:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == RoleEnum.clinic and (not current_user.clinic_account or booking.clinic_id != current_user.clinic_account.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == RoleEnum.doctor and (not current_user.doctor_account or booking.doctor_id != current_user.doctor_account.id):
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return enrich_booking_for_output(booking)


@router.patch("/{booking_id}/confirm", response_model=BookingOut)
def confirm_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "doctor", "admin"))
):
    """Confirm a booking. Only from pending."""
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.deleted_at == None).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if current_user.role == RoleEnum.clinic and booking.clinic_id != current_user.clinic_account.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == RoleEnum.doctor and booking.doctor_id != current_user.doctor_account.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if booking.booking_status != BookingStatusEnum.pending:
        raise HTTPException(status_code=400, detail="Only pending bookings can be confirmed")
        
    booking.booking_status = BookingStatusEnum.confirmed
    db.commit()
    db.refresh(booking)
    return enrich_booking_for_output(booking)


@router.patch("/{booking_id}/complete", response_model=BookingOut)
def complete_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("clinic", "doctor", "admin"))
):
    """Complete a booking. Only from confirmed."""
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.deleted_at == None).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if current_user.role == RoleEnum.clinic and booking.clinic_id != current_user.clinic_account.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == RoleEnum.doctor and booking.doctor_id != current_user.doctor_account.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if booking.booking_status != BookingStatusEnum.confirmed:
        raise HTTPException(status_code=400, detail="Only confirmed bookings can be completed")
        
    booking.booking_status = BookingStatusEnum.completed
    db.commit()
    db.refresh(booking)
    return enrich_booking_for_output(booking)


@router.patch("/{booking_id}/cancel")
def cancel_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.deleted_at == None).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if current_user.role == RoleEnum.user and booking.user_id != current_user.uuid:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == RoleEnum.clinic and booking.clinic_id != current_user.clinic_account.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == RoleEnum.doctor and booking.doctor_id != current_user.doctor_account.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if booking.booking_status == BookingStatusEnum.completed:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed booking")
        
    booking.booking_status = BookingStatusEnum.cancelled
    
    if booking.slot:
        booking.slot.slot_status = SlotStatusEnum.available
        
    db.commit()
    return {"message": "Booking cancelled"}


@router.patch("/{booking_id}/reschedule", response_model=BookingOut)
def reschedule_booking(
    booking_id: str,
    payload: BookingReschedule,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Swap slot for a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.deleted_at == None).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if current_user.role == RoleEnum.user and booking.user_id != current_user.uuid:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == RoleEnum.clinic and booking.clinic_id != current_user.clinic_account.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == RoleEnum.doctor and booking.doctor_id != current_user.doctor_account.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if booking.booking_status not in [BookingStatusEnum.pending, BookingStatusEnum.confirmed]:
        raise HTTPException(status_code=400, detail="Cannot reschedule completed or cancelled booking")
        
    new_slot = db.query(AppointmentSlot).filter(
        AppointmentSlot.id == payload.new_slot_id,
        AppointmentSlot.deleted_at == None
    ).first()
    
    if not new_slot:
        raise HTTPException(status_code=404, detail="New slot not found")
    if new_slot.slot_status != SlotStatusEnum.available:
        raise HTTPException(status_code=409, detail="New slot is not available")
        
    old_slot = booking.slot
    if old_slot:
        old_slot.slot_status = SlotStatusEnum.available
        
    new_slot.slot_status = SlotStatusEnum.booked
    
    booking.slot_id = new_slot.id
    
    db.commit()
    db.refresh(booking)
    return enrich_booking_for_output(booking)


@router.patch("/{booking_id}/rate")
def rate_booking(
    booking_id: str,
    rating: int = Query(..., ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rate a completed booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.deleted_at == None).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.user_id != current_user.uuid:
        raise HTTPException(status_code=403, detail="Only the patient can rate the booking")
        
    if booking.booking_status != BookingStatusEnum.completed:
        raise HTTPException(status_code=400, detail="Can only rate completed bookings")
        
    # In the new model, we use DoctorRating model
    from models import DoctorRating
    new_rating = DoctorRating(
        booking_id=booking.id,
        doctor_id=booking.doctor_id,
        rating_score=rating
    )
    db.add(new_rating)
    
    doctor = booking.doctor
    if doctor:
        if doctor.rating_count is None:
            doctor.rating_count = 0
            doctor.average_rating = 0.0
            
        total_rating = doctor.average_rating * doctor.rating_count
        doctor.rating_count += 1
        doctor.average_rating = (total_rating + rating) / doctor.rating_count
        
    db.commit()
    return {"message": "Rating submitted successfully"}


@router.get("/{booking_id}/invoice")
def get_invoice(
    booking_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate invoice."""
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.deleted_at == None).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    return {
        "invoice_id": f"INV-{booking.id[:8]}",
        "booking_id": booking.id,
        "amount": 500.0,
        "tax": 50.0,
        "total": 550.0,
        "pdf_url": f"https://api.example.com/invoices/INV-{booking.id[:8]}.pdf"
    }

