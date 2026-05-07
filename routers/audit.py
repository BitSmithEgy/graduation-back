from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import User, AuditLog
from schemas import AuditLogOut
from utils import require_admin

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/", response_model=List[AuditLogOut])
def list_audit_logs(
    user_id: Optional[str] = None,
    clinic_id: Optional[str] = None,
    action_type: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List audit logs (Admin only)."""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if clinic_id:
        query = query.filter(AuditLog.clinic_id == clinic_id)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
        
    return query.order_by(AuditLog.created_at.desc()).limit(100).all()

@router.get("/{audit_id}", response_model=AuditLogOut)
def get_audit_log(
    audit_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get specific audit log entry (Admin only)."""
    log = db.query(AuditLog).filter(AuditLog.audit_id == audit_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log entry not found")
    return log
