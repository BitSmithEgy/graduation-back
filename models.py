from sqlalchemy import (
    Column, String, Boolean, Date, TIMESTAMP, Time,
    Enum, ForeignKey, INTEGER, Float, JSON, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func
import enum
import uuid


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def gen_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class LanguageEnum(enum.Enum):
    en = "en"
    ar = "ar"


class RoleEnum(enum.Enum):
    user   = "user"
    clinic = "clinic"
    admin  = "admin"
    doctor = "doctor"


class GenderEnum(enum.Enum):
    male    = "male"
    female  = "female"
    other   = "other"


class ActionTypeEnum(enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    login  = "login"
    logout = "logout"


class DataQualityEnum(enum.Enum):
    good = "good"
    fair = "fair"
    poor = "poor"


class ViewPositionEnum(enum.Enum):
    PA  = "PA"
    AP  = "AP"
    LAT = "LAT"


class SeverityEnum(enum.Enum):
    mild     = "mild"
    moderate = "moderate"
    severe   = "severe"


class SlotStatusEnum(enum.Enum):
    available = "available"
    blocked   = "blocked"
    cancelled = "cancelled"
    booked    = "booked"


class BookingStatusEnum(enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class InvitationStatusEnum(enum.Enum):
    pending   = "pending"
    accepted  = "accepted"
    rejected  = "rejected"
    expired   = "expired"


class LanguageSpokenEnum(enum.Enum):
    en   = "en"
    ar   = "ar"
    both = "both"


# ─────────────────────────────────────────────
# RBAC  –  roles & user_roles
# ─────────────────────────────────────────────

class Role(Base):
    """
    Fine-grained roles beyond the inline RoleEnum on User.
    Supports bilingual role names + description.
    """
    __tablename__ = "roles"

    role_id        = Column(INTEGER, primary_key=True, autoincrement=True)
    role_name_en   = Column(String(100), unique=True, nullable=False)
    role_name_ar   = Column(String(100), unique=True, nullable=False)
    description_en = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)

    user_roles = relationship("UserRole", back_populates="role")


class UserRole(Base):
    """
    Junction: many users ↔ many roles.
    """
    __tablename__ = "user_roles"

    user_id    = Column(String(36), ForeignKey("users.uuid"),  primary_key=True)
    role_id    = Column(INTEGER,    ForeignKey("roles.role_id"), primary_key=True)
    assigned_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


# ─────────────────────────────────────────────
# Core user
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    uuid          = Column(String(36), primary_key=True, unique=True, nullable=False, default=gen_uuid)
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

    # ── relationships ──
    user_roles     = relationship("UserRole",      back_populates="user")
    profile        = relationship("UserProfile",   back_populates="user", uselist=False)
    oauth_accounts = relationship("OAuthAccount",  back_populates="user")
    sessions       = relationship("Session",       back_populates="user")
    clinic_account = relationship("Clinic",        back_populates="user", uselist=False)
    doctor_account = relationship("Doctor",        back_populates="user", uselist=False)
    bookings       = relationship("Booking",       back_populates="user")
    medical_record = relationship("MedicalRecord", back_populates="user", uselist=False)
    diagnostics    = relationship("Diagnostic",    back_populates="user")
    audit_logs     = relationship("AuditLog",      back_populates="user")
    chat_sessions  = relationship("ChatSession",   back_populates="user")


# ─────────────────────────────────────────────
# OAuth
# ─────────────────────────────────────────────

class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    oauth_account_id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id          = Column(String(36), ForeignKey("users.uuid"), nullable=False)
    provider_name    = Column(String(50),  nullable=False)   # google / apple / …
    created_at       = Column(TIMESTAMP,   server_default=func.now())
    updated_at       = Column(TIMESTAMP,   server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="oauth_accounts")


# ─────────────────────────────────────────────
# Sessions
# ─────────────────────────────────────────────

class Session(Base):
    __tablename__ = "sessions"

    session_id       = Column(String(36), primary_key=True, default=gen_uuid)
    user_id          = Column(String(36), ForeignKey("users.uuid"), nullable=False)
    token_hash       = Column(String(255), nullable=False)
    device_info      = Column(Text,        nullable=True)
    ip_address       = Column(String(45),  nullable=True)
    issued_at        = Column(TIMESTAMP,   server_default=func.now())
    expires_at       = Column(TIMESTAMP,   nullable=False)
    primary_language = Column(Enum(LanguageEnum, name="session_lang_enum"), nullable=True)
    revoked_at       = Column(TIMESTAMP,   nullable=True)

    user          = relationship("User",        back_populates="sessions")
    chat_sessions = relationship("ChatSession", back_populates="session")


# ─────────────────────────────────────────────
# Audit log
# ─────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id      = Column(String(36), primary_key=True, default=gen_uuid)
    user_id       = Column(String(36), ForeignKey("users.uuid"), nullable=True)
    clinic_id     = Column(String(36), ForeignKey("clinics.id"), nullable=True)
    clinic_name   = Column(String(255), nullable=True)
    clinic_address = Column(String(255), nullable=True)
    action_type   = Column(Enum(ActionTypeEnum, name="action_type_enum"), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id   = Column(String(36),  nullable=True)
    ip_address    = Column(String(45),  nullable=True)
    location      = Column(JSON,        nullable=True)
    old_values    = Column(JSON,        nullable=True)
    new_values    = Column(JSON,        nullable=True)
    specialty_name_en = Column(String(255), nullable=True)
    description   = Column(Text,        nullable=True)
    created_at    = Column(TIMESTAMP,   server_default=func.now())
    used_agent    = Column(TIMESTAMP,   nullable=True)

    user   = relationship("User",   back_populates="audit_logs")
    clinic = relationship("Clinic", back_populates="audit_logs")


# ─────────────────────────────────────────────
# User profile
# ─────────────────────────────────────────────

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id      = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)

    date_of_birth = Column(Date, nullable=True)
    gender        = Column(Enum(GenderEnum, name="gender_enum"), nullable=True)

    height_cm               = Column(Float,       nullable=True)
    weight_kg               = Column(Float,       nullable=True)
    blood_type              = Column(String(3),   nullable=True)
    known_allergies         = Column(Text,        nullable=True)
    chronic_conditions      = Column(Text,        nullable=True)
    data_quality_flag       = Column(Enum(DataQualityEnum, name="data_quality_enum"), nullable=True)
    image_path              = Column(String(500), nullable=True)
    delete_reason           = Column(String(500), nullable=True)
    emergency_contact_name  = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20),  nullable=True)

    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    user = relationship("User", back_populates="profile")


# ─────────────────────────────────────────────
# Clinic
# ─────────────────────────────────────────────

class Clinic(Base):
    __tablename__ = "clinics"

    id      = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)

    name     = Column(String(255), nullable=False)
    address  = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    phone    = Column(String(20),  nullable=False)
    email    = Column(String(255), nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    user          = relationship("User",            back_populates="clinic_account")
    doctor_clinics = relationship("DoctorClinic",   back_populates="clinic")          # many-to-many
    slots         = relationship("AppointmentSlot", back_populates="clinic")
    bookings      = relationship("Booking",         back_populates="clinic")
    audit_logs     = relationship("AuditLog",        back_populates="clinic")


# ─────────────────────────────────────────────
# Specializations
# ─────────────────────────────────────────────

class Specialization(Base):
    __tablename__ = "specializations"

    id             = Column(String(36), primary_key=True, default=gen_uuid)
    name_en        = Column(String(100), nullable=False)
    name_ar        = Column(String(100), nullable=False)
    description_en = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    created_at     = Column(TIMESTAMP, server_default=func.now())
    updated_at     = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at     = Column(TIMESTAMP, nullable=True)

    doctors    = relationship("Doctor",   back_populates="specialization")


# ─────────────────────────────────────────────
# Doctor
# ─────────────────────────────────────────────

class Doctor(Base):
    """
    A doctor may belong to zero, one, or many clinics.
    The many-to-many link lives in DoctorClinic.
    clinic_id here is REMOVED – use DoctorClinic instead.
    """
    __tablename__ = "doctors"

    id                = Column(String(36), primary_key=True, default=gen_uuid)
    user_id           = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)
    specialization_id = Column(String(36), ForeignKey("specializations.id"), nullable=True)

    full_name                = Column(String(255), nullable=False)
    language_spoken          = Column(Enum(LanguageSpokenEnum, name="language_spoken_enum"), nullable=True)
    bio_en                   = Column(Text,        nullable=True)
    bio_ar                   = Column(Text,        nullable=True)
    consultation_price_egp   = Column(Float,       nullable=True)
    years_of_experience      = Column(INTEGER,     nullable=True)
    license_number           = Column(String(255), nullable=True)
    is_verified              = Column(Boolean,     default=False)
    average_rating           = Column(Float,       nullable=True)
    rating_count             = Column(INTEGER,     nullable=True)
    is_active                = Column(Boolean,     default=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    user           = relationship("User",             back_populates="doctor_account")
    specialization = relationship("Specialization",   back_populates="doctors")
    doctor_clinics = relationship("DoctorClinic",     back_populates="doctor")        # many-to-many
    availability   = relationship("DoctorAvailability", back_populates="doctor")
    bookings       = relationship("Booking",          back_populates="doctor")
    ratings        = relationship("DoctorRating",     back_populates="doctor")
    slots          = relationship("AppointmentSlot",  back_populates="doctor")


# ─────────────────────────────────────────────
# Doctor ↔ Clinic   (many-to-many junction)
# ─────────────────────────────────────────────

class DoctorClinic(Base):
    """
    A doctor can work at multiple clinics; a clinic can have multiple doctors.
    Data isolation: every availability / slot / booking references BOTH
    doctor_id and clinic_id (clinic_id nullable for independent doctors).
    """
    __tablename__ = "doctor_clinics"
    __table_args__ = (
        UniqueConstraint("doctor_id", "clinic_id", name="uq_doctor_clinic"),
    )

    id         = Column(String(36), primary_key=True, default=gen_uuid)
    doctor_id  = Column(String(36), ForeignKey("doctors.id"),  nullable=False)
    clinic_id  = Column(String(36), ForeignKey("clinics.id"),  nullable=False)
    is_primary = Column(Boolean, default=False)   # marks the doctor's "home" clinic
    is_active  = Column(Boolean, default=True)
    joined_at  = Column(TIMESTAMP, server_default=func.now())
    left_at    = Column(TIMESTAMP, nullable=True)

    doctor = relationship("Doctor", back_populates="doctor_clinics")
    clinic = relationship("Clinic", back_populates="doctor_clinics")


class ClinicDoctorInvitation(Base):
    """
    Clinic sends an invitation to a doctor.
    If the doctor accepts, a record is created in DoctorClinic.
    """
    __tablename__ = "clinic_doctor_invitations"

    id           = Column(String(36), primary_key=True, default=gen_uuid)
    clinic_id    = Column(String(36), ForeignKey("clinics.id"),  nullable=False)
    doctor_id    = Column(String(36), ForeignKey("doctors.id"),  nullable=False)
    status       = Column(Enum(InvitationStatusEnum), default=InvitationStatusEnum.pending)
    message      = Column(Text, nullable=True)
    created_at   = Column(TIMESTAMP, server_default=func.now())
    responded_at = Column(TIMESTAMP, nullable=True)

    clinic = relationship("Clinic")
    doctor = relationship("Doctor")


# ─────────────────────────────────────────────
# Doctor availability
# ─────────────────────────────────────────────

class DoctorAvailability(Base):
    """
    Defines the recurring weekly schedule for a doctor.
    clinic_id is nullable → supports independent (no-clinic) doctors.
    """
    __tablename__ = "doctor_availability"

    id        = Column(String(36), primary_key=True, default=gen_uuid)
    doctor_id = Column(String(36), ForeignKey("doctors.id"),  nullable=False)
    clinic_id = Column(String(36), ForeignKey("clinics.id"),  nullable=True)   # NULL = independent

    day_of_week           = Column(INTEGER, nullable=False)   # 0=Mon … 6=Sun
    start_time            = Column(Time,    nullable=False)
    end_time              = Column(Time,    nullable=False)
    slot_duration_minutes = Column(INTEGER, nullable=False)
    is_active             = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    doctor = relationship("Doctor", back_populates="availability")
    clinic = relationship("Clinic")
    slots  = relationship("AppointmentSlot", back_populates="availability", cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# Appointment slot
# ─────────────────────────────────────────────

class AppointmentSlot(Base):
    """
    A concrete time slot generated from DoctorAvailability.
    clinic_id nullable → independent doctor slots have no clinic.
    """
    __tablename__ = "appointment_slots"

    id              = Column(String(36), primary_key=True, default=gen_uuid)
    doctor_id       = Column(String(36), ForeignKey("doctors.id"),           nullable=False)
    clinic_id       = Column(String(36), ForeignKey("clinics.id"),           nullable=True)
    availability_id = Column(String(36), ForeignKey("doctor_availability.id"), nullable=False)

    slot_date       = Column(Date,   nullable=False)
    slot_start_time = Column(Time,   nullable=False)
    slot_end_time   = Column(Time,   nullable=False)
    slot_status     = Column(Enum(SlotStatusEnum, name="slot_status_enum"), nullable=False,
                             default=SlotStatusEnum.available)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    doctor       = relationship("Doctor",            back_populates="slots")
    clinic       = relationship("Clinic",            back_populates="slots")
    availability = relationship("DoctorAvailability", back_populates="slots")
    bookings     = relationship("Booking",           back_populates="slot")


# ─────────────────────────────────────────────
# Booking
# ─────────────────────────────────────────────

class BookingSource(Base):
    __tablename__ = "booking_sources"

    id              = Column(String(36), primary_key=True, default=gen_uuid)
    source_code     = Column(String(50),  nullable=False, unique=True)
    source_name_en  = Column(String(100), nullable=False)
    source_name_ar  = Column(String(100), nullable=True)
    created_at      = Column(TIMESTAMP, server_default=func.now())

    bookings = relationship("Booking", back_populates="booking_source")


class Booking(Base):
    """
    clinic_id nullable → bookings with independent doctors have no clinic.
    doctor_id is now explicit for fast lookups without joining slots.
    """
    __tablename__ = "bookings"

    id        = Column(String(36), primary_key=True, default=gen_uuid)
    user_id   = Column(String(36), ForeignKey("users.uuid"),         nullable=False)
    doctor_id = Column(String(36), ForeignKey("doctors.id"),         nullable=False)
    clinic_id = Column(String(36), ForeignKey("clinics.id"),         nullable=True)
    slot_id   = Column(String(36), ForeignKey("appointment_slots.id"), nullable=False)
    booking_source_id = Column(String(36), ForeignKey("booking_sources.id"), nullable=True)

    booking_status     = Column(Enum(BookingStatusEnum, name="booking_status_enum"),
                                nullable=False, default=BookingStatusEnum.pending)
    payment_reference  = Column(String(255), nullable=True)
    payment_status     = Column(String(50),  nullable=True)
    cancellation_reason = Column(Text,       nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    user           = relationship("User",          back_populates="bookings")
    doctor         = relationship("Doctor",        back_populates="bookings")
    clinic         = relationship("Clinic",        back_populates="bookings")
    slot           = relationship("AppointmentSlot", back_populates="bookings")
    booking_source = relationship("BookingSource", back_populates="bookings")
    appointment_notes = relationship("AppointmentNotes", back_populates="booking", uselist=False)
    roles          = relationship("AppointmentRole",  back_populates="booking")
    ratings        = relationship("DoctorRating",     back_populates="booking")


# ─────────────────────────────────────────────
# Appointment notes
# ─────────────────────────────────────────────

class AppointmentNotes(Base):
    __tablename__ = "appointment_notes"

    id         = Column(String(36), primary_key=True, default=gen_uuid)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    notes      = Column(Text,       nullable=True)
    created_at = Column(TIMESTAMP,  server_default=func.now())
    updated_at = Column(TIMESTAMP,  server_default=func.now(), onupdate=func.now())

    booking = relationship("Booking", back_populates="appointment_notes")


# ─────────────────────────────────────────────
# Appointment roles   (who did what in a booking)
# ─────────────────────────────────────────────

class AppointmentRole(Base):
    __tablename__ = "appointment_roles"

    id             = Column(String(36), primary_key=True, default=gen_uuid)
    booking_id     = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    role           = Column(Text,        nullable=True)
    role_language  = Column(String(10),  nullable=True)
    created_at     = Column(TIMESTAMP,   server_default=func.now())
    updated_at     = Column(TIMESTAMP,   server_default=func.now(), onupdate=func.now())

    booking = relationship("Booking", back_populates="roles")


# ─────────────────────────────────────────────
# Doctor ratings
# ─────────────────────────────────────────────

class DoctorRating(Base):
    __tablename__ = "doctor_ratings"

    id           = Column(String(36), primary_key=True, default=gen_uuid)
    booking_id   = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    doctor_id    = Column(String(36), ForeignKey("doctors.id"),  nullable=False)
    rating_score = Column(INTEGER,    nullable=False)             # e.g. 1-5
    review_text  = Column(Text,       nullable=True)
    review_language = Column(String(10), nullable=True)
    created_at   = Column(TIMESTAMP,  server_default=func.now())
    updated_at   = Column(TIMESTAMP,  server_default=func.now(), onupdate=func.now())

    booking = relationship("Booking", back_populates="ratings")
    doctor  = relationship("Doctor",  back_populates="ratings")


# ─────────────────────────────────────────────
# Medical records
# ─────────────────────────────────────────────

class RecordType(Base):
    __tablename__ = "record_type"

    type_id    = Column(String(36), primary_key=True, default=gen_uuid)
    record_id  = Column(String(36), ForeignKey("medical_records.id"), nullable=False)
    reference_id = Column(String(36), nullable=True)   # FK to any resource
    added_at   = Column(TIMESTAMP, server_default=func.now())

    medical_record = relationship("MedicalRecord", back_populates="record_types")


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id           = Column(String(36), primary_key=True, default=gen_uuid)
    user_id      = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)
    record       = Column(JSON,       nullable=False, default=dict)
    generated_at = Column(TIMESTAMP,  server_default=func.now(), onupdate=func.now())

    user         = relationship("User",       back_populates="medical_record")
    record_types = relationship("RecordType", back_populates="medical_record")


# ─────────────────────────────────────────────
# Diagnostics (diabetes / risk model)
# ─────────────────────────────────────────────

class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id              = Column(String(36), primary_key=True, default=gen_uuid)
    user_id         = Column(String(36), ForeignKey("users.uuid"), nullable=False)
    diagnostic_name = Column(String(255), nullable=True)

    pregnancies                = Column(INTEGER, nullable=True)
    glucose                    = Column(INTEGER, nullable=True)
    blood_pressure             = Column(INTEGER, nullable=True)
    skin_thickness             = Column(INTEGER, nullable=True)
    insulin                    = Column(INTEGER, nullable=True)
    bmi                        = Column(Float,   nullable=True)
    diabetes_pedigree_function = Column(Float,   nullable=True)
    age                        = Column(INTEGER, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    user   = relationship("User",             back_populates="diagnostics")
    result = relationship("DiagnosticResult", back_populates="diagnostic", uselist=False)


class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"

    id            = Column(String(36), primary_key=True, default=gen_uuid)
    diagnostic_id = Column(String(36), ForeignKey("diagnostics.id"), nullable=False)
    risk_level    = Column(String(50), nullable=False)
    confidence    = Column(Float,      nullable=False)
    created_at    = Column(TIMESTAMP,  server_default=func.now())

    diagnostic = relationship("Diagnostic", back_populates="result")


# ─────────────────────────────────────────────
# Radiology
# ─────────────────────────────────────────────

class Radiology(Base):
    __tablename__ = "radiology"

    id          = Column(String(36), primary_key=True, default=gen_uuid)
    user_id     = Column(String(36), ForeignKey("users.uuid"), nullable=False)
    image_path  = Column(String(500), nullable=False)
    image_hash  = Column(String(255), nullable=True)
    body_part   = Column(String(100), nullable=True)
    view_position = Column(Enum(ViewPositionEnum, name="view_position_enum"), nullable=True)
    data_quality_flag = Column(Enum(DataQualityEnum, name="radiology_quality_enum"), nullable=True)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    deleted_at  = Column(TIMESTAMP, nullable=True)

    user     = relationship("User")
    findings = relationship("RadiologyFinding", back_populates="radiology")


class RadiologyFinding(Base):
    __tablename__ = "radiology_findings"

    id           = Column(String(36), primary_key=True, default=gen_uuid)
    radiology_id = Column(String(36), ForeignKey("radiology.id"), nullable=False)
    finding_name = Column(String(255), nullable=False)
    finding_range   = Column(String(255), nullable=True)
    confidence_score = Column(Float,     nullable=True)
    severity     = Column(Enum(SeverityEnum, name="severity_enum"), nullable=True)
    bounding_box = Column(JSON,          nullable=True)   # {x, y, w, h}
    created_at   = Column(TIMESTAMP,     server_default=func.now())

    radiology = relationship("Radiology", back_populates="findings")


# ─────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    chat_session_id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id         = Column(String(36), ForeignKey("users.uuid"), nullable=False)
    session_id      = Column(String(36), ForeignKey("sessions.session_id"), nullable=True)
    vendor_llm      = Column(String(100), nullable=True)   # openai / groq / …
    started_at      = Column(TIMESTAMP,   server_default=func.now())
    ended_at        = Column(TIMESTAMP,   nullable=True)

    user     = relationship("User",    back_populates="chat_sessions")
    session  = relationship("Session", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id              = Column(String(36), primary_key=True, default=gen_uuid)
    chat_session_id = Column(String(36), ForeignKey("chat_sessions.chat_session_id"), nullable=False)
    sender_role     = Column(String(20),  nullable=False)   # "user" | "assistant"
    message_content = Column(Text,        nullable=False)
    language_detected = Column(String(10), nullable=True)
    sequence_number = Column(INTEGER,     nullable=True)
    created_at      = Column(TIMESTAMP,   server_default=func.now())

    chat_session  = relationship("ChatSession", back_populates="messages")
    symptom_tags  = relationship("SymptomTag",  back_populates="message")


# ─────────────────────────────────────────────
# Symptom tags  (NLP extraction from chat)
# ─────────────────────────────────────────────

class SymptomTag(Base):
    __tablename__ = "symptom_tags"

    symptom_tag_id    = Column(String(36), primary_key=True, default=gen_uuid)
    message_id        = Column(String(36), ForeignKey("chat_messages.id"), nullable=False)
    symptom_name_en   = Column(String(255), nullable=True)
    symptom_name_ar   = Column(String(255), nullable=True)
    confidence_score  = Column(Float,       nullable=True)
    created_at        = Column(TIMESTAMP,   server_default=func.now())

    message = relationship("ChatMessage", back_populates="symptom_tags")