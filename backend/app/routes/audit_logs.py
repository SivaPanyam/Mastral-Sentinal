from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User
from app.schemas import AuditLogOut
from app.crud import AuditLogRepository
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("/", response_model=List[AuditLogOut])
def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter logs by user ID"),
    resource_id: Optional[str] = Query(None, description="Filter logs by resource ID"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "Security Analyst", "SRE"]))
):
    """Retrieve system audit logs. Requires Admin, Security Analyst, or SRE role."""
    if user_id:
        return AuditLogRepository.get_by_user(db, user_id, limit)
    elif resource_id:
        return AuditLogRepository.get_by_resource(db, resource_id, limit)
    else:
        return AuditLogRepository.get_all(db, limit)
