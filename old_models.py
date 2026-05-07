from sqlalchemy import Column, String, Boolean, Date, TIMESTAMP, Time, Enum, ForeignKey, INTEGER, Float, JSON, Text
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func
import enum
import uuid

class LanguageEnum(enum.Enum):
    en = "en"
    ar = "ar"


class RoleEnum(enum.Enum):
    user   = "user"
    clinic = "clinic"
    admin  = "admin"
    doctor = "doctor"


class User(Base):
    __tablename__ = "users"

    uuid = Column(
        String(36),
        primary_key=True,
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    email         = Column(String(255), unique=True, nullable=False, index=True)
    phone         = Column(String(20),  unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(255), nullable=False)
    language_preference = Column(
        Enum(LanguageEnum, name="language_enum"),
        nullable=True,
        default=LanguageEnum.en
    )
    role = Column(
        Enum(RoleEnum, name="role_enum"),
        nullable=False,
        default=RoleEnum.user
    )
    is_active  = Column(Boolean,   default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    profile     = relationship("UserProfile", back_populates="user", uselist=False)
    clinic      = relationship("Clinic",      back_populates="user", uselist=False)
    bookings    = relationship("Booking",     back_populates="user", uselist=True)  
    medical_record = relationship("MedicalRecord", back_populates="user", uselist=False)
    doctor_account = relationship("Doctors", back_populates="user", uselist=False)
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id      = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)

    date_of_birth  = Column(Date,        nullable=True)
    gender         = Column(String(10),  nullable=True)
    blood_type     = Column(String(3),   nullable=True)
    height         = Column(Float,  nullable=True)
    weight         = Column(Float,  nullable=True)
    known_allergies     = Column(String(255), nullable=True)
    chronic_conditions  = Column(String(255), nullable=True)
    emergency_contact_name  = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20),  nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    user = relationship("User", back_populates="profile")



class Clinic(Base):
    __tablename__ = "clinics"

    id      = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)

    name     = Column(String(255), nullable=False)
    address  = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    phone    = Column(String(20),  nullable=False)
    email    = Column(String(255), nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    user = relationship("User", back_populates="clinic")
    doctor = relationship("Doctors", back_populates="clinic")
    slots = relationship("AppointmentSlot", back_populates="clinic")
    bookings = relationship("Booking", back_populates="clinic")

class Diagnotics(Base):
    __tablename__ = "diagnostics"

    id = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.uuid"), nullable=False)
    pregnancies = Column(INTEGER, nullable=True)
    glucose = Column(INTEGER, nullable=True)
    blood_pressure = Column(INTEGER, nullable=True)
    skin_thickness = Column(INTEGER, nullable=True)
    insulin = Column(INTEGER, nullable=True)
    bmi = Column(Float, nullable=True)
    diabetes_pedigree_function = Column(Float, nullable=True)
    age = Column(INTEGER, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    result = relationship("DiagnoticsResults", back_populates="diagnostic", uselist=False)

class DiagnoticsResults(Base):
    __tablename__ = "diagnostic_results"

    id = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    diagnostic_id = Column(String(36), ForeignKey("diagnostics.id"), nullable=False)
    risk_level = Column(String(50), nullable=False)
    confidece = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    diagnostic = relationship("Diagnotics", back_populates="result")

class Specializations(Base):
    __tablename__ = "specializations"
    id = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name_en = Column(String(100), nullable=False)
    name_ar = Column(String(100), nullable=False)
    description_en = Column(String(255), nullable=True)
    description_ar = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    doctor = relationship("Doctors", back_populates="specialization")

class LanguageSpoken(enum.Enum):
    en = "en"
    ar = "ar"


class Doctors(Base):
    __tablename__ = "doctors"

    id = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)
    clinic_id = Column(String(36), ForeignKey("clinics.id"), nullable=True)
    full_name = Column(String(255), nullable=False)
    specialization_id = Column(String(36), ForeignKey("specializations.id"), nullable=True)
    language_spoken = Column(Enum(LanguageSpoken, name="language_spoken_enum"), nullable=True)
    bio_en = Column(String(1000), nullable=True)
    bio_ar = Column(String(1000), nullable=True)
    consultation_price_egp = Column(Float, nullable=True)
    years_of_experience = Column(INTEGER, nullable=True)
    license_number = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    avarage_rating = Column(Float, nullable=True)
    rating_count = Column(INTEGER, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    user = relationship("User", back_populates="doctor_account")
    clinic = relationship("Clinic", back_populates="doctor")
    specialization = relationship("Specializations", back_populates="doctor")
    availability = relationship("DoctorAvailability", back_populates="doctor", uselist=True)

    
class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"
    id = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(INTEGER, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(INTEGER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    doctor = relationship("Doctors", back_populates="availability")
    slots  = relationship("AppointmentSlot", back_populates="availability")  

class SlotStatusEnum(enum.Enum):
    available = "available"
    blocked = "blocked"
    cancelled = "cancelled"
    booked = "booked"

class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"
    id = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String(36), ForeignKey("clinics.id"), nullable=False)
    availability_id = Column(String(36), ForeignKey("doctor_availability.id"), nullable=False)
    slot_date = Column(Date, nullable=False)
    slot_start_time = Column(Time, nullable=False)
    slot_end_time = Column(Time, nullable=False)
    slot_status = Column(Enum(SlotStatusEnum, name="slot_status_enum"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    clinic = relationship("Clinic", back_populates="slots")
    availability = relationship("DoctorAvailability", back_populates="slots")
    bookings = relationship("Booking", back_populates="slot")
    
class BookingStatusEnum(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    clinic_id = Column(String(36), ForeignKey("clinics.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.uuid"), nullable=False)
    slot_id = Column(String(36), ForeignKey("appointment_slots.id"), nullable=False)
    booking_status = Column(Enum(BookingStatusEnum, name="booking_status_enum"), nullable=False)
    cancellation_reason = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    clinic = relationship("Clinic", back_populates="bookings")
    user = relationship("User", back_populates="bookings")
    slot = relationship("AppointmentSlot", back_populates="bookings")
    notes = relationship("AppointmentNotes", back_populates="booking", uselist=False)

class AppointmentNotes(Base):
    __tablename__ = "appointment_notes"
    id = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    notes = Column(String(1000), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    booking = relationship("Booking", back_populates="notes")

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id         = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id    = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)
    record     = Column(JSON, nullable=False, default=dict)
    generated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="medical_record")