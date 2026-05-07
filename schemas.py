from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional, List
from datetime import date, datetime, time
import enum


# ═══════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════

class LanguageEnum(str, enum.Enum):
    en = "en"
    ar = "ar"


class RoleEnum(str, enum.Enum):
    user   = "user"
    clinic = "clinic"
    admin  = "admin"
    doctor = "doctor"


class GenderEnum(str, enum.Enum):
    male   = "male"
    female = "female"
    other  = "other"


class LanguageSpokenEnum(str, enum.Enum):
    en   = "en"
    ar   = "ar"
    both = "both"


class SlotStatusEnum(str, enum.Enum):
    available = "available"
    blocked   = "blocked"
    cancelled = "cancelled"
    booked    = "booked"


class BookingStatusEnum(str, enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class InvitationStatusEnum(str, enum.Enum):
    pending   = "pending"
    accepted  = "accepted"
    rejected  = "rejected"
    expired   = "expired"


class SeverityEnum(str, enum.Enum):
    mild     = "mild"
    moderate = "moderate"
    severe   = "severe"


class ViewPositionEnum(str, enum.Enum):
    PA  = "PA"
    AP  = "AP"
    LAT = "LAT"


class DataQualityEnum(str, enum.Enum):
    good = "good"
    fair = "fair"
    poor = "poor"


class ActionTypeEnum(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    login  = "login"
    logout = "logout"


# ═══════════════════════════════════════════════════════════════
# ROLE  &  USER-ROLE
# ═══════════════════════════════════════════════════════════════

class RoleBase(BaseModel):
    role_name_en:   str
    role_name_ar:   str
    description_en: Optional[str] = None
    description_ar: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    role_name_en:   Optional[str] = None
    role_name_ar:   Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None


class RoleOut(RoleBase):
    role_id: int
    model_config = ConfigDict(from_attributes=True)


class UserRoleOut(BaseModel):
    user_id:     str
    role_id:     int
    assigned_at: datetime
    role:        RoleOut
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# USER
# ═══════════════════════════════════════════════════════════════

class UserBase(BaseModel):
    email:               EmailStr
    phone:               str
    full_name:           str
    language_preference: Optional[LanguageEnum] = LanguageEnum.en


class UserCreate(UserBase):
    password: str
    role:     RoleEnum = RoleEnum.user


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class UserUpdate(BaseModel):
    phone:               Optional[str]          = None
    full_name:           Optional[str]          = None
    password:            Optional[str]          = None
    language_preference: Optional[LanguageEnum] = None


class UserOut(UserBase):
    uuid:       str
    role:       RoleEnum
    is_active:  bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Registration payloads ──────────────────────────────────────

class UserProfileCreate(BaseModel):
    date_of_birth:           Optional[date]       = None
    gender:                  Optional[GenderEnum] = None
    blood_type:              Optional[str]        = None
    height_cm:               Optional[float]      = None
    weight_kg:               Optional[float]      = None
    known_allergies:         Optional[str]        = None
    chronic_conditions:      Optional[str]        = None
    emergency_contact_name:  Optional[str]        = None
    emergency_contact_phone: Optional[str]        = None


class ClinicCreate(BaseModel):
    name:     str
    address:  str
    phone:    str
    email:    EmailStr
    location: Optional[str] = None


class UserRegister(BaseModel):
    """Normal user registration"""
    email:               EmailStr
    phone:               str
    full_name:           str
    password:            str
    language_preference: Optional[LanguageEnum]   = LanguageEnum.en
    profile:             Optional[UserProfileCreate] = None


class ClinicRegister(BaseModel):
    """Clinic account registration"""
    email:               EmailStr
    phone:               str
    full_name:           str
    password:            str
    language_preference: Optional[LanguageEnum] = LanguageEnum.en
    clinic:              ClinicCreate


class DoctorRegister(BaseModel):
    """
    Independent doctor registration (no clinic at sign-up).
    A clinic link can be added later via DoctorClinic endpoints.
    """
    email:               EmailStr
    phone:               str
    full_name:           str
    password:            str
    language_preference: Optional[LanguageEnum] = LanguageEnum.en
    specialization_id:        Optional[str]          = None
    language_spoken:          Optional[LanguageSpokenEnum] = None
    bio_en:                   Optional[str]          = None
    bio_ar:                   Optional[str]          = None
    consultation_price_egp:   Optional[float]        = None
    years_of_experience:      Optional[int]          = None
    license_number:           Optional[str]          = None


# ═══════════════════════════════════════════════════════════════
# USER PROFILE
# ═══════════════════════════════════════════════════════════════

class UserProfileUpdate(BaseModel):
    date_of_birth:           Optional[date]       = None
    gender:                  Optional[GenderEnum] = None
    blood_type:              Optional[str]        = None
    height_cm:               Optional[float]      = None
    weight_kg:               Optional[float]      = None
    known_allergies:         Optional[str]        = None
    chronic_conditions:      Optional[str]        = None
    emergency_contact_name:  Optional[str]        = None
    emergency_contact_phone: Optional[str]        = None
    image_path:              Optional[str]        = None


class UserProfileOut(UserProfileCreate):
    id:                Optional[str]       = None
    user_id:           str
    image_path:        Optional[str]       = None
    data_quality_flag: Optional[DataQualityEnum] = None
    updated_at:        Optional[datetime]  = None
    deleted_at:        Optional[datetime]  = None
    model_config = ConfigDict(from_attributes=True)


# ── Composite user responses ───────────────────────────────────

class UserWithProfileOut(UserOut):
    """GET /me  →  role = user"""
    profile: Optional[UserProfileOut] = None
    model_config = ConfigDict(from_attributes=True)


class UserWithClinicOut(UserOut):
    """GET /me  →  role = clinic"""
    clinic_account: Optional["ClinicOut"] = None
    model_config = ConfigDict(from_attributes=True)


class UserWithDoctorOut(UserOut):
    """GET /me  →  role = doctor"""
    doctor_account: Optional["DoctorOut"] = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# TOKEN
# ═══════════════════════════════════════════════════════════════

class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserWithProfileOut | UserWithClinicOut | UserWithDoctorOut


# ═══════════════════════════════════════════════════════════════
# SESSION
# ═══════════════════════════════════════════════════════════════

class SessionOut(BaseModel):
    session_id:       str
    user_id:          str
    device_info:      Optional[str]          = None
    ip_address:       Optional[str]          = None
    issued_at:        datetime
    expires_at:       datetime
    primary_language: Optional[LanguageEnum] = None
    revoked_at:       Optional[datetime]     = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# OAUTH
# ═══════════════════════════════════════════════════════════════

class OAuthAccountOut(BaseModel):
    oauth_account_id: str
    user_id:          str
    provider_name:    str
    created_at:       datetime
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# AUDIT LOG
# ═══════════════════════════════════════════════════════════════

class AuditLogOut(BaseModel):
    audit_id:      str
    user_id:       Optional[str]            = None
    clinic_id:     Optional[str]            = None
    action_type:   ActionTypeEnum
    resource_type: Optional[str]            = None
    resource_id:   Optional[str]            = None
    ip_address:    Optional[str]            = None
    location:      Optional[dict]           = None
    old_values:    Optional[dict]           = None
    new_values:    Optional[dict]           = None
    description:   Optional[str]            = None
    created_at:    datetime
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# CLINIC
# ═══════════════════════════════════════════════════════════════

class ClinicBase(BaseModel):
    name:     str
    address:  str
    phone:    str
    email:    EmailStr
    location: Optional[str] = None


class ClinicUpdate(BaseModel):
    name:     Optional[str]      = None
    address:  Optional[str]      = None
    phone:    Optional[str]      = None
    email:    Optional[EmailStr] = None
    location: Optional[str]      = None


class ClinicOut(ClinicBase):
    id:         str
    user_id:    str
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ClinicMiniOut(BaseModel):
    id:      str
    name:    str
    address: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# SPECIALIZATION
# ═══════════════════════════════════════════════════════════════

class SpecializationBase(BaseModel):
    name_en:        str
    name_ar:        str
    description_en: Optional[str] = None
    description_ar: Optional[str] = None


class SpecializationCreate(SpecializationBase):
    pass


class SpecializationUpdate(BaseModel):
    name_en:        Optional[str] = None
    name_ar:        Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None


class SpecializationOut(SpecializationBase):
    id:         str
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# DOCTOR
# ═══════════════════════════════════════════════════════════════

class DoctorBase(BaseModel):
    full_name:              str
    specialization_id:      Optional[str]              = None
    language_spoken:        Optional[LanguageSpokenEnum] = None
    bio_en:                 Optional[str]              = None
    bio_ar:                 Optional[str]              = None
    consultation_price_egp: Optional[float]            = None
    years_of_experience:    Optional[int]              = None
    license_number:         Optional[str]              = None
    is_active:              Optional[bool]             = True


class DoctorCreate(DoctorBase):
    """Used by an admin or the doctor themselves (no clinic yet)."""
    pass


class DoctorUpdate(BaseModel):
    specialization_id:      Optional[str]              = None
    language_spoken:        Optional[LanguageSpokenEnum] = None
    bio_en:                 Optional[str]              = None
    bio_ar:                 Optional[str]              = None
    consultation_price_egp: Optional[float]            = None
    years_of_experience:    Optional[int]              = None
    license_number:         Optional[str]              = None
    is_active:              Optional[bool]             = None


class DoctorOut(DoctorBase):
    id:             str
    user_id:        str
    is_verified:    bool
    average_rating: Optional[float] = None
    rating_count:   Optional[int]   = None
    created_at:     datetime
    updated_at:     Optional[datetime] = None
    deleted_at:     Optional[datetime] = None
    specialization: Optional[SpecializationOut] = None
    model_config = ConfigDict(from_attributes=True)


class DoctorMiniOut(BaseModel):
    id:        str
    full_name: str
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# DOCTOR ↔ CLINIC  (many-to-many)
# ═══════════════════════════════════════════════════════════════

class DoctorClinicCreate(BaseModel):
    """
    Link a doctor to a clinic.
    Called by a clinic admin or system admin.
    """
    doctor_id:  str
    clinic_id:  str
    is_primary: bool = False


class DoctorClinicUpdate(BaseModel):
    is_primary: Optional[bool] = None
    is_active:  Optional[bool] = None
    left_at:    Optional[datetime] = None


class DoctorClinicOut(BaseModel):
    id:         str
    doctor_id:  str
    clinic_id:  str
    is_primary: bool
    is_active:  bool
    joined_at:  datetime
    left_at:    Optional[datetime] = None
    doctor:     Optional[DoctorMiniOut]  = None
    clinic:     Optional[ClinicMiniOut]  = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# DOCTOR AVAILABILITY
# ═══════════════════════════════════════════════════════════════

class AvailabilityCreate(BaseModel):
    """
    clinic_id is optional — omit for independent doctors.
    day_of_week: 0 = Monday … 6 = Sunday
    """
    clinic_id:             Optional[str] = None
    day_of_week:           int
    start_time:            time
    end_time:              time
    slot_duration_minutes: int = 30

    @field_validator("day_of_week")
    @classmethod
    def validate_day(cls, v: int) -> int:
        if v not in range(7):
            raise ValueError("day_of_week must be 0–6")
        return v


class AvailabilityUpdate(BaseModel):
    clinic_id:             Optional[str]  = None
    day_of_week:           Optional[int]  = None
    start_time:            Optional[time] = None
    end_time:              Optional[time] = None
    slot_duration_minutes: Optional[int]  = None
    is_active:             Optional[bool] = None


class AvailabilityOut(BaseModel):
    id:                    str
    doctor_id:             str
    clinic_id:             Optional[str]  = None
    day_of_week:           int
    start_time:            time
    end_time:              time
    slot_duration_minutes: int
    is_active:             bool
    created_at:            datetime
    updated_at:            Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# APPOINTMENT SLOT
# ═══════════════════════════════════════════════════════════════

class SlotCreate(BaseModel):
    availability_id: str
    slot_date:       date
    slot_start_time: time
    slot_end_time:   time


class SlotGenerateRequest(BaseModel):
    """Generate slots in bulk from a doctor's availability schedule."""
    doctor_id:  str
    clinic_id:  Optional[str] = None   # None → independent doctor
    from_date:  date
    to_date:    date


class SlotStatusUpdate(BaseModel):
    slot_status: SlotStatusEnum
    notes:       Optional[str] = None


class SlotOut(BaseModel):
    id:              str
    doctor_id:       str
    clinic_id:       Optional[str]      = None
    availability_id: str
    slot_date:       date
    slot_start_time: time
    slot_end_time:   time
    slot_status:     SlotStatusEnum
    created_at:      datetime
    updated_at:      Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class SlotGenerationResponse(BaseModel):
    generated: int
    skipped:   int
    slots:     List[SlotOut]
    model_config = ConfigDict(from_attributes=True)


class SlotMiniOut(BaseModel):
    id:              str
    slot_date:       date
    slot_start_time: time
    slot_end_time:   time
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# BOOKING SOURCE
# ═══════════════════════════════════════════════════════════════

class BookingSourceCreate(BaseModel):
    source_code:    str
    source_name_en: str
    source_name_ar: Optional[str] = None


class BookingSourceOut(BaseModel):
    id:             str
    source_code:    str
    source_name_en: str
    source_name_ar: Optional[str] = None
    created_at:     datetime
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# BOOKING
# ═══════════════════════════════════════════════════════════════

class BookingCreate(BaseModel):
    slot_id:           str
    notes:             Optional[str] = None
    booking_language:  str           = "ar"
    booking_source_id: Optional[str] = None


class BookingReschedule(BaseModel):
    new_slot_id: str


class BookingStatusUpdate(BaseModel):
    booking_status:      BookingStatusEnum
    cancellation_reason: Optional[str] = None


class BookingOut(BaseModel):
    id:                  str
    user_id:             str
    doctor_id:           str
    clinic_id:           Optional[str]         = None
    slot:                SlotMiniOut
    doctor:              DoctorMiniOut
    clinic:              Optional[ClinicMiniOut] = None
    booking_status:      BookingStatusEnum
    payment_reference:   Optional[str]         = None
    payment_status:      Optional[str]         = None
    cancellation_reason: Optional[str]         = None
    created_at:          datetime
    updated_at:          Optional[datetime]    = None
    deleted_at:          Optional[datetime]    = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# APPOINTMENT NOTES
# ═══════════════════════════════════════════════════════════════

class AppointmentNotesCreate(BaseModel):
    notes: str


class AppointmentNotesUpdate(BaseModel):
    notes: Optional[str] = None


class AppointmentNotesOut(BaseModel):
    id:         str
    booking_id: str
    notes:      Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# APPOINTMENT ROLE
# ═══════════════════════════════════════════════════════════════

class AppointmentRoleCreate(BaseModel):
    role:          str
    role_language: Optional[str] = None


class AppointmentRoleOut(BaseModel):
    id:            str
    booking_id:    str
    role:          Optional[str] = None
    role_language: Optional[str] = None
    created_at:    datetime
    updated_at:    Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# DOCTOR RATING
# ═══════════════════════════════════════════════════════════════

class DoctorRatingCreate(BaseModel):
    booking_id:      str
    rating_score:    int
    review_text:     Optional[str] = None
    review_language: Optional[str] = None

    @field_validator("rating_score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v not in range(1, 6):
            raise ValueError("rating_score must be between 1 and 5")
        return v


class DoctorRatingOut(BaseModel):
    id:              str
    booking_id:      str
    doctor_id:       str
    rating_score:    int
    review_text:     Optional[str]      = None
    review_language: Optional[str]      = None
    created_at:      datetime
    updated_at:      Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# MEDICAL RECORD
# ═══════════════════════════════════════════════════════════════

class RecordTypeCreate(BaseModel):
    reference_id: Optional[str] = None


class RecordTypeOut(BaseModel):
    type_id:      str
    record_id:    str
    reference_id: Optional[str] = None
    added_at:     datetime
    model_config = ConfigDict(from_attributes=True)


class MedicalRecordOut(BaseModel):
    id:           str
    user_id:      str
    record:       dict
    generated_at: datetime
    record_types: List[RecordTypeOut] = []
    model_config = ConfigDict(from_attributes=True)


class MedicalRecordUpdate(BaseModel):
    record: dict


# ═══════════════════════════════════════════════════════════════
# DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════

class DiabetesRequest(BaseModel):
    pregnancies:                int
    glucose:                    float
    blood_pressure:             float
    skin_thickness:             float
    insulin:                    float
    bmi:                        float
    diabetes_pedigree_function: float
    age:                        int


class DiagnosticResultOut(BaseModel):
    id:            str
    diagnostic_id: str
    risk_level:    str
    confidence:    float
    created_at:    datetime
    model_config = ConfigDict(from_attributes=True)


class DiagnosticOut(BaseModel):
    id:                         str
    user_id:                    str
    diagnostic_name:            Optional[str]   = None
    pregnancies:                Optional[int]   = None
    glucose:                    Optional[int]   = None
    blood_pressure:             Optional[int]   = None
    skin_thickness:             Optional[int]   = None
    insulin:                    Optional[int]   = None
    bmi:                        Optional[float] = None
    diabetes_pedigree_function: Optional[float] = None
    age:                        Optional[int]   = None
    created_at:                 datetime
    result:                     Optional[DiagnosticResultOut] = None
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# RADIOLOGY
# ═══════════════════════════════════════════════════════════════

class RadiologyCreate(BaseModel):
    body_part:         Optional[str]             = None
    view_position:     Optional[ViewPositionEnum] = None
    data_quality_flag: Optional[DataQualityEnum]  = None
    # image_path is set server-side after file upload


class RadiologyFindingOut(BaseModel):
    id:               str
    radiology_id:     str
    finding_name:     str
    finding_range:    Optional[str]          = None
    confidence_score: Optional[float]        = None
    severity:         Optional[SeverityEnum] = None
    bounding_box:     Optional[dict]         = None
    created_at:       datetime
    model_config = ConfigDict(from_attributes=True)


class RadiologyOut(BaseModel):
    id:                str
    user_id:           str
    image_path:        str
    image_hash:        Optional[str]             = None
    body_part:         Optional[str]             = None
    view_position:     Optional[ViewPositionEnum] = None
    data_quality_flag: Optional[DataQualityEnum]  = None
    uploaded_at:       datetime
    deleted_at:        Optional[datetime]         = None
    findings:          List[RadiologyFindingOut]  = []
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# CHAT
# ═══════════════════════════════════════════════════════════════

class ChatSessionCreate(BaseModel):
    vendor_llm: Optional[str] = None


class ChatSessionOut(BaseModel):
    chat_session_id: str
    user_id:         str
    session_id:      Optional[str]      = None
    vendor_llm:      Optional[str]      = None
    started_at:      datetime
    ended_at:        Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseModel):
    message_content: str
    sender_role:     str = "user"   # "user" | "assistant"


class ChatMessageOut(BaseModel):
    id:                str
    chat_session_id:   str
    sender_role:       str
    message_content:   str
    language_detected: Optional[str] = None
    sequence_number:   Optional[int] = None
    created_at:        datetime
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# SYMPTOM TAGS
# ═══════════════════════════════════════════════════════════════

class SymptomTagOut(BaseModel):
    symptom_tag_id:   str
    message_id:       str
    symptom_name_en:  Optional[str]   = None
    symptom_name_ar:  Optional[str]   = None
    confidence_score: Optional[float] = None
    created_at:       datetime
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════
# INVITATIONS
# ═══════════════════════════════════════════════════════════════

class InvitationCreate(BaseModel):
    doctor_id: str
    message: Optional[str] = None

class InvitationOut(BaseModel):
    id: str
    clinic_id: str
    doctor_id: str
    status: InvitationStatusEnum
    message: Optional[str] = None
    created_at: datetime
    responded_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ── Rebuild forward-referenced models ─────────────────────────
UserWithClinicOut.model_rebuild()
UserWithDoctorOut.model_rebuild()
TokenOut.model_rebuild()