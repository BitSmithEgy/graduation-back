from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Role, UserRole, User
from schemas import RoleOut, RoleCreate, RoleUpdate, UserRoleOut
from utils import require_admin

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("/", response_model=List[RoleOut])
def list_roles(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """List all available roles (Admin only)."""
    return db.query(Role).all()

@router.post("/", response_model=RoleOut, status_code=201)
def create_role(payload: RoleCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Create a new role (Admin only)."""
    if db.query(Role).filter(Role.role_name_en == payload.role_name_en).first():
        raise HTTPException(status_code=400, detail="Role already exists")
        
    role = Role(**payload.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.post("/assign", status_code=201)
def assign_role(user_id: str, role_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Assign a role to a user (Admin only)."""
    # Check if assignment already exists
    exists = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="User already has this role")
        
    user_role = UserRole(user_id=user_id, role_id=role_id)
    db.add(user_role)
    db.commit()
    return {"message": "Role assigned successfully"}

@router.delete("/unassign")
def unassign_role(user_id: str, role_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Remove a role from a user (Admin only)."""
    user_role = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role_id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail="Role assignment not found")
        
    db.delete(user_role)
    db.commit()
    return {"message": "Role unassigned successfully"}

@router.get("/user/{user_id}", response_model=List[UserRoleOut])
def get_user_roles(user_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Get all roles for a specific user (Admin only)."""
    return db.query(UserRole).filter(UserRole.user_id == user_id).all()
