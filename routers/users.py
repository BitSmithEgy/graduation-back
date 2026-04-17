from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserProfile, Clinic, RoleEnum
from schemas import (
    UserRegister, ClinicRegister,
    UserWithProfileOut, UserWithClinicOut,
    UserUpdate, UserProfileCreate, UserProfileUpdate, UserProfileOut,
    ClinicCreate, ClinicUpdate, ClinicOut,
    UserOut, UserLogin, TokenOut
)
from utils import hash_password, verify_password, create_access_token, get_current_user, require_admin
from datetime import timedelta, datetime
from typing import Union

router = APIRouter(prefix="/users", tags=["users"])



def _build_user_out(user: User) -> Union[UserWithProfileOut, UserWithClinicOut]:
    """Return the right enriched schema based on the user's role."""
    if user.role == RoleEnum.clinic:
        return UserWithClinicOut.model_validate(user)
    return UserWithProfileOut.model_validate(user)



@router.post("/register/user", response_model=UserWithProfileOut, status_code=201)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    user = User(
        **payload.model_dump(exclude={"password", "profile"}),
        password_hash=hash_password(payload.password),
        role=RoleEnum.user,
    )
    db.add(user)
    db.flush()

    profile_data = payload.profile.model_dump() if payload.profile else {}
    db.add(UserProfile(user_id=user.uuid, **profile_data))

    db.commit()
    db.refresh(user)
    return UserWithProfileOut.model_validate(user)


@router.post("/register/clinic", response_model=UserWithClinicOut, status_code=201)
def register_clinic(payload: ClinicRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    user = User(
        **payload.model_dump(exclude={"password", "clinic"}),
        password_hash=hash_password(payload.password),
        role=RoleEnum.clinic,
    )
    db.add(user)
    db.flush()

    db.add(Clinic(user_id=user.uuid, **payload.clinic.model_dump()))

    db.commit()
    db.refresh(user)
    return UserWithClinicOut.model_validate(user)



@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    if user.deleted_at is not None:
        raise HTTPException(status_code=403, detail="Account has been deleted")

    token = create_access_token(
        data={"user_id": user.uuid, "role": user.role.value},
        expires_delta=timedelta(minutes=30),
    )
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")

    return TokenOut(access_token=token, user=_build_user_out(user))


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}



@router.get("/me", response_model=Union[UserWithProfileOut, UserWithClinicOut])
def get_me(current_user: User = Depends(get_current_user)):
    return _build_user_out(current_user)


@router.put("/me", response_model=Union[UserWithProfileOut, UserWithClinicOut])
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "password":
            setattr(current_user, "password_hash", hash_password(value))
        else:
            setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return _build_user_out(current_user)


@router.delete("/me", status_code=200)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Account deleted"}



@router.get("/me/profile", response_model=UserProfileOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users have a profile")
    if not current_user.profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return current_user.profile


@router.post("/me/profile", response_model=UserProfileOut, status_code=201)
def create_my_profile(
    data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users can have a profile")
    if current_user.profile:
        raise HTTPException(status_code=400, detail="Profile already exists, use PATCH to update")

    profile = UserProfile(user_id=current_user.uuid, **data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/me/profile", response_model=UserProfileOut)
def update_my_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != RoleEnum.user:
        raise HTTPException(status_code=403, detail="Only regular users have a profile")
    if not current_user.profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user.profile, key, value)

    db.commit()
    db.refresh(current_user.profile)
    return current_user.profile



@router.get("/me/clinic", response_model=ClinicOut)
def get_my_clinic(current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.clinic:
        raise HTTPException(status_code=403, detail="Only clinic accounts have clinic details")
    if not current_user.clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return current_user.clinic


@router.patch("/me/clinic", response_model=ClinicOut)
def update_my_clinic(
    data: ClinicUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != RoleEnum.clinic:
        raise HTTPException(status_code=403, detail="Only clinic accounts can update clinic details")
    if not current_user.clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user.clinic, key, value)

    db.commit()
    db.refresh(current_user.clinic)
    return current_user.clinic



@router.get("/", response_model=list[Union[UserWithProfileOut, UserWithClinicOut]])
def get_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.deleted_at.is_(None)).all()
    return [_build_user_out(u) for u in users]


@router.get("/{user_id}", response_model=Union[UserWithProfileOut, UserWithClinicOut])
def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.uuid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _build_user_out(user)


@router.patch("/{user_id}/role", response_model=Union[UserWithProfileOut, UserWithClinicOut])
def set_user_role(
    user_id: str,
    role: RoleEnum,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.uuid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    db.refresh(user)
    return _build_user_out(user)


@router.patch("/{user_id}/switch", response_model=Union[UserWithProfileOut, UserWithClinicOut])
def toggle_user_active(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.uuid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return _build_user_out(user)


@router.delete("/{user_id}", status_code=200)
def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.uuid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "User deleted"}