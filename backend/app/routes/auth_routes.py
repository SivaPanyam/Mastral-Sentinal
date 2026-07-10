from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    verify_password,
    get_current_user
)
from app.schemas import UserLogin, Token, TokenRefreshRequest
from app.crud import UserRepository
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from app.config import settings
from app.models.auth_models import UserSession
from app.limiter import limiter
import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Setup OAuth
config_data = {
    'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID if hasattr(settings, 'GOOGLE_CLIENT_ID') else '',
    'GOOGLE_CLIENT_SECRET': settings.GOOGLE_CLIENT_SECRET if hasattr(settings, 'GOOGLE_CLIENT_SECRET') else ''
}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate SRE admins and operators, returning JWT access and refresh tokens."""
    user = UserRepository.get_by_email(db, user_data.email)
    if not user or not verify_password(user_data.password, user.hashed_password):
        # We could add an audit log here for failed login
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password configured inside Mastra Sentinel"
        )
    
    # Audit Log for successful login
    from app.models.audit_log import AuditLog
    audit_log = AuditLog(
        userId=user.id,
        action="LOGIN_SUCCESS",
        resourceType="Authentication",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"email": user.email},
        response_status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()
    
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "name": user.name}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email,
        "role": user.role,
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=Token)
def refresh_token_endpoint(req: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Refresh an expired access token using a valid refresh token."""
    payload = verify_refresh_token(req.refresh_token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")
        
    user = UserRepository.get_by_email(db, email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "name": user.name}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.email}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email,
        "role": user.role,
        "refresh_token": new_refresh_token
    }

@router.post("/logout")
def logout(request: Request, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Log out user and record audit log."""
    user = UserRepository.get_by_email(db, current_user["email"])
    if user:
        from app.models.audit_log import AuditLog
        audit_log = AuditLog(
            userId=user.id,
            action="LOGOUT",
            resourceType="Authentication",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details={"email": user.email},
            response_status="SUCCESS"
        )
        db.add(audit_log)
        db.commit()
    return {"status": "Logged out successfully"}

@router.get("/login/{provider}")
async def login_via_sso(request: Request, provider: str):
    """Initiate SSO login flow."""
    redirect_uri = request.url_for('auth_callback', provider=provider)
    if provider == 'google':
        return await oauth.google.authorize_redirect(request, redirect_uri)
    raise HTTPException(status_code=400, detail="Unsupported SSO provider")

@router.get("/callback/{provider}")
async def auth_callback(request: Request, provider: str, db: Session = Depends(get_db)):
    """Callback for SSO login flow."""
    if provider == 'google':
        try:
            token = await oauth.google.authorize_access_token(request)
            user_info = token.get('userinfo')
        except Exception:
            raise HTTPException(status_code=400, detail="Authentication failed")
            
        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="No email provided by SSO")
            
        user = UserRepository.get_by_email(db, email)
        if not user:
            raise HTTPException(status_code=403, detail="User not registered in Sentinel")
            
        # Create successful login audit log
        from app.models.audit_log import AuditLog
        audit_log = AuditLog(
            userId=user.id,
            action="LOGIN_SUCCESS_SSO",
            resourceType="Authentication",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details={"email": user.email, "provider": provider},
            response_status="SUCCESS"
        )
        db.add(audit_log)
        db.commit()
        
        access_token = create_access_token(data={"sub": user.email, "role": user.role, "name": user.name})
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "email": user.email,
            "role": user.role,
            "refresh_token": refresh_token,
            "message": "SSO Login successful"
        }
    
    raise HTTPException(status_code=400, detail="Unsupported SSO provider")

@router.post("/reset-password")
def reset_password(email: str, db: Session = Depends(get_db)):
    """Mock endpoint for password reset."""
    return {"status": "Password reset email sent if user exists."}
