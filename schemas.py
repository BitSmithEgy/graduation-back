from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
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