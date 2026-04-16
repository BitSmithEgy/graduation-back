from sqlalchemy import Column, String, Boolean, Date, TIMESTAMP, Enum
from database import Base
from sqlalchemy.sql import func
import enum
import uuid


class LanguageEnum(enum.Enum):
    en = "en"
    ar = "ar"


class RoleEnum(enum.Enum):
    user  = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    uuid = Column(
        String(36),
        primary_key=True,
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    email     = Column(String(255), unique=True, nullable=False, index=True)
    phone     = Column(String(20),  unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender    = Column(String(10), nullable=True)

    language_preference = Column(
        Enum(LanguageEnum, name="language_enum"),
        nullable=True,
        default=LanguageEnum.en
    )
    role = Column(
        Enum(RoleEnum, name="role_enum"),
        nullable=False,
        default=RoleEnum.user       # every new account starts as "user"
    )

    is_active  = Column(Boolean,   default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)