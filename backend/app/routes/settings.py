from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Settings
from app.schemas import SettingsCreate, SettingsOut
from app.crud import SettingsRepository
from app.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/", response_model=SettingsOut)
def get_user_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's settings."""
    settings = SettingsRepository.get_by_user_id(db, current_user.id)
    if not settings:
        # Create default settings if they don't exist yet
        settings = Settings(userId=current_user.id)
        settings = SettingsRepository.create(db, settings)
    return settings

@router.put("/", response_model=SettingsOut)
def update_user_settings(settings_in: SettingsCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update settings for the current user."""
    settings = SettingsRepository.get_by_user_id(db, current_user.id)
    
    if not settings:
        settings = Settings(userId=current_user.id)
        settings = SettingsRepository.create(db, settings)
        
    # Update fields
    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
        
    return SettingsRepository.update(db, settings)
