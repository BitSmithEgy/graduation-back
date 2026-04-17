from sqlalchemy import Column, String, Boolean, Date, TIMESTAMP, Enum, ForeignKey
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

    user_roles  = relationship("UserRoles",   back_populates="user")
    profile     = relationship("UserProfile", back_populates="user", uselist=False)
    clinic      = relationship("Clinic",      back_populates="user", uselist=False)


class Roles(Base):
    __tablename__ = "roles"

    id        = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    role_name = Column(String(50), unique=True, nullable=False)

    user_roles = relationship("UserRoles", back_populates="role")


class UserRoles(Base):
    __tablename__ = "user_roles"

    id      = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.uuid"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"),   nullable=False)

    user = relationship("User",  back_populates="user_roles")
    role = relationship("Roles", back_populates="user_roles")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id      = Column(String(36), primary_key=True, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)  # unique = one-to-one

    date_of_birth  = Column(Date,        nullable=True)
    gender         = Column(String(10),  nullable=True)
    blood_type     = Column(String(3),   nullable=True)
    height         = Column(String(10),  nullable=True)
    weight         = Column(String(10),  nullable=True)
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
    user_id = Column(String(36), ForeignKey("users.uuid"), unique=True, nullable=False)  # unique = one-to-one

    name     = Column(String(255), nullable=False)
    address  = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    phone    = Column(String(20),  nullable=False)
    email    = Column(String(255), nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP, nullable=True)

    user = relationship("User", back_populates="clinic")