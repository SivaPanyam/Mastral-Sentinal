from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User
from app.schemas import UserOut
from app.crud import UserRepository
from app.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all active users."""
    return UserRepository.get_all(db)

@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Soft delete a user by ID (Admin only)."""
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete users.")
    
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    UserRepository.soft_delete(db, user)
    return
