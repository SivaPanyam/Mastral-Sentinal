import hashlib
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, require_role
from app.crud import UserRepository
from app.models.auth_models import ApiKey
from app.limiter import limiter
from pydantic import BaseModel

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

class ApiKeyCreate(BaseModel):
    name: str
    scopes: Optional[List[str]] = None

class ApiKeyOut(BaseModel):
    id: str
    name: str
    prefix: str
    scopes: Optional[List[str]]
    is_active: bool

class ApiKeyCreateResponse(ApiKeyOut):
    key: str # Only returned once

@router.post("/", response_model=ApiKeyCreateResponse)
@limiter.limit("10/minute")
def create_api_key(
    request: Request,
    payload: ApiKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key for programmatic access."""
    user = UserRepository.get_by_email(db, current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate raw key
    raw_key = f"mastra_{uuid.uuid4().hex}{uuid.uuid4().hex}"
    
    # Hash for storage
    key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    
    api_key = ApiKey(
        user_id=user.id,
        name=payload.name,
        key_hash=key_hash,
        prefix=raw_key[:10],
        scopes=payload.scopes or []
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    # Audit logging
    from app.models.audit_log import AuditLog
    audit_log = AuditLog(
        userId=user.id,
        action="API_KEY_CREATED",
        resourceType="Authentication",
        resourceId=api_key.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"name": payload.name},
        response_status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return {
        "id": api_key.id,
        "name": api_key.name,
        "prefix": api_key.prefix,
        "scopes": api_key.scopes,
        "is_active": api_key.is_active,
        "key": raw_key
    }

@router.get("/", response_model=List[ApiKeyOut])
def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all active API keys for the current user."""
    user = UserRepository.get_by_email(db, current_user["email"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    keys = db.query(ApiKey).filter(ApiKey.user_id == user.id, ApiKey.is_active == True).all()
    return keys

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    request: Request,
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an existing API key."""
    user = UserRepository.get_by_email(db, current_user["email"])
    key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    key.is_active = False
    db.commit()
    
    # Audit logging
    from app.models.audit_log import AuditLog
    audit_log = AuditLog(
        userId=user.id,
        action="API_KEY_REVOKED",
        resourceType="Authentication",
        resourceId=key.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"name": key.name},
        response_status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()
    
    return None
