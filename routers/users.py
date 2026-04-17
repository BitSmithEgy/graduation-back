from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User, RoleEnum
from schemas import UserCreate, UserOut, UserLogin, UserUpdate
from utils import hash_password, verify_password, create_access_token, get_current_user, require_admin, require_user
from datetime import timedelta, datetime

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        **user.dict(exclude={"password"}),
        password_hash=hash_password(user.password),
        role=RoleEnum.user 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"user_id": db_user.uuid},
        expires_delta=timedelta(minutes=30)
    )
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return {"message": "Login successful", "access_token": token}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}



@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for key, value in data.dict(exclude_unset=True).items():
        if key == "password":
            setattr(current_user, "password_hash", hash_password(value))
        else:
            setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me")
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Account deleted"}



@router.get("/", response_model=list[UserOut])
def get_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all users — admin only."""
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Get any user by ID — admin only."""
    user = db.query(User).filter(User.uuid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}/role", response_model=UserOut)
def set_user_role(
    user_id: str,
    role: RoleEnum,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Promote or demote any user's role — admin only."""
    user = db.query(User).filter(User.uuid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/switch", response_model=UserOut)
def toggle_user_active(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle is_active for any user — admin only."""
    user = db.query(User).filter(User.uuid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Soft-delete any user — admin only."""
    user = db.query(User).filter(User.uuid == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "User deleted"}