from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
import enum


class LanguageEnum(str, enum.Enum):
    en = "en"
    ar = "ar"


class RoleEnum(str, enum.Enum):
    user  = "user"
    admin = "admin"


class UserBase(BaseModel):
    email: EmailStr
    phone: str
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    language_preference: Optional[LanguageEnum] = LanguageEnum.en


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    language_preference: Optional[LanguageEnum] = None


class UserOut(UserBase):
    uuid: str
    role: RoleEnum
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True