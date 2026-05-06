from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import date, datetime, time
import enum



class LanguageEnum(str, enum.Enum):
    en = "en"
    ar = "ar"


class RoleEnum(str, enum.Enum):
    user   = "user"
    clinic = "clinic"
    admin  = "admin"


class UserBase(BaseModel):
    email: EmailStr
    phone: str
    full_name: str
    language_preference: Optional[LanguageEnum] = LanguageEnum.en


class UserCreate(UserBase):
    password: str
    role: RoleEnum = RoleEnum.user


class UserLogin(BaseModel):
    email: EmailStr
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

    class Config:
        from_attributes = True


class UserProfileBase(BaseModel):
    date_of_birth:           Optional[date] = None
    gender:                  Optional[str]  = None
    blood_type:              Optional[str]  = None
    height:                  Optional[str]  = None
    weight:                  Optional[str]  = None
    known_allergies:         Optional[str]  = None
    chronic_conditions:      Optional[str]  = None
    emergency_contact_name:  Optional[str]  = None
    emergency_contact_phone: Optional[str]  = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass 


class UserProfileOut(UserProfileBase):
    id:         str
    user_id:    str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ClinicBase(BaseModel):
    name:     str
    address:  str
    phone:    str
    email:    EmailStr
    location: Optional[str] = None


class ClinicCreate(ClinicBase):
    pass


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

    class Config:
        from_attributes = True


class RoleOut(BaseModel):
    id:        str
    role_name: str

    class Config:
        from_attributes = True


class UserRoleOut(BaseModel):
    id:      str
    user_id: str
    role_id: str
    role:    RoleOut

    class Config:
        from_attributes = True



class UserWithProfileOut(UserOut):
    """Returned after login / GET /me  →  role = user"""
    profile: Optional[UserProfileOut] = None

    class Config:
        from_attributes = True


class UserWithClinicOut(UserOut):
    """Returned after login / GET /me  →  role = clinic"""
    clinic: Optional[ClinicOut] = None

    class Config:
        from_attributes = True



class UserRegister(BaseModel):
    """Normal user registration payload"""
    email:               EmailStr
    phone:               str
    full_name:           str
    password:            str
    language_preference: Optional[LanguageEnum] = LanguageEnum.en
    profile:             Optional[UserProfileCreate] = None


class ClinicRegister(BaseModel):
    """Clinic registration payload"""
    email:               EmailStr
    phone:               str
    full_name:           str
    password:            str
    language_preference: Optional[LanguageEnum] = LanguageEnum.en
    clinic:              ClinicCreate



class TokenOut(BaseModel):
    access_token:  str
    token_type:    str = "bearer"
    user:          UserWithProfileOut | UserWithClinicOut



class DiabetesRequest(BaseModel):
    pregnancies: int
    glucose: float
    blood_pressure: float
    skin_thickness: float
    insulin: float
    bmi: float
    diabetes_pedigree_function: float
    age: int

class SpecializationBase(BaseModel):
    name_en: str
    name_ar: str
    description_en: Optional[str] = None
    description_ar: Optional[str] = None

class SpecializationCreate(SpecializationBase):
    pass

class SpecializationUpdate(BaseModel):
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None

class SpecializationOut(SpecializationBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DoctorBase(BaseModel):
    specialization_id: str
    full_name: str
    language_spoken: Optional[LanguageEnum] = None
    bio_en: Optional[str] = None
    bio_ar: Optional[str] = None
    consultation_price_egp: Optional[float] = None
    years_of_experiance: Optional[int] = None
    license_number: Optional[str] = None
    is_active: Optional[bool] = True

class DoctorCreate(DoctorBase):
    """
    Schema for a clinic to create a doctor. 
    `clinic_id` is intentionally omitted because it should be inferred from the logged-in clinic user.
    """
    pass

class DoctorUpdate(BaseModel):
    specialization_id: Optional[str] = None
    language_spoken: Optional[LanguageEnum] = None
    bio_en: Optional[str] = None
    bio_ar: Optional[str] = None
    consultation_price_egp: Optional[float] = None
    years_of_experiance: Optional[int] = None
    license_number: Optional[str] = None
    is_active: Optional[bool] = None

class DoctorOut(DoctorBase):
    id: str
    clinic_id: Optional[str] = None
    is_verified: bool
    avg_rating: float
    rating_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ── AVAILABILITY ──────────────────────────────────────────────────
class AvailabilityCreate(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int = 30

class AvailabilityUpdate(BaseModel):
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    slot_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None

class AvailabilityOut(BaseModel):
    id: str
    doctor_id: str
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ── SLOTS ──────────────────────────────────────────────────────────
class SlotStatusEnum(str, enum.Enum):
    available = "available"
    blocked = "blocked"
    cancelled = "cancelled"
    booked = "booked"

class SlotCreate(BaseModel):
    availability_id: str
    slot_date: date
    slot_start_time: time
    slot_end_time: time
    notes: Optional[str] = None

class SlotGenerateRequest(BaseModel):
    doctor_id: str
    from_date: date
    to_date: date

class SlotStatusUpdate(BaseModel):
    slot_status: SlotStatusEnum
    notes: Optional[str] = None

class SlotOut(BaseModel):
    id: str
    availability_id: Optional[str]
    clinic_id: Optional[str]
    slot_date: date
    slot_start_time: time
    slot_end_time: time
    slot_status: SlotStatusEnum
    notes: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ── BOOKINGS ───────────────────────────────────────────────────────
class PaymentPreferenceEnum(str, enum.Enum):
    cash = "cash"
    card = "card"
    insurance = "insurance"

class BookingStatusEnum(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"

class BookingCreate(BaseModel):
    slot_id: str
    notes: Optional[str] = None
    booking_language: str = "ar"
    # payment_preference: PaymentPreferenceEnum = PaymentPreferenceEnum.cash
    # booking_source_id: Optional[str] = None

class BookingReschedule(BaseModel):
    new_slot_id: str

class BookingStatusUpdate(BaseModel):
    booking_status: BookingStatusEnum
    cancellation_reason: Optional[str] = None

class SlotMiniOut(BaseModel):
    id: str
    slot_date: date
    slot_start_time: time
    slot_end_time: time
    model_config = ConfigDict(from_attributes=True)

class DoctorMiniOut(BaseModel):
    id: str
    full_name: str
    model_config = ConfigDict(from_attributes=True)

class BookingOut(BaseModel):
    id: str
    slot: SlotMiniOut
    user_id: str
    doctor: DoctorMiniOut
    clinic_id: Optional[str]
    booking_status: BookingStatusEnum
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)