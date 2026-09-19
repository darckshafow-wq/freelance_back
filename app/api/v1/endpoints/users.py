from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.models.user import Profile
from app.schemas.user import UserOut, ProfileOut
from app.services.upload_service import delete_old_file

router = APIRouter()


# Schema for updating user profile
class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPersonalUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile"""
    return current_user


@router.put("/me/profile", response_model=UserOut)
def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile (bio, skills, avatar)"""
    
    # Update user fields
    if profile_update.full_name:
        current_user.full_name = profile_update.full_name
    
    # Update or create profile
    if not current_user.profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        current_user.profile = profile
    
    if profile_update.bio is not None:
        current_user.profile.bio = profile_update.bio
    
    if profile_update.skills is not None:
        current_user.profile.skills = profile_update.skills
    
    if profile_update.avatar_url is not None:
        # Supprimer l'ancien avatar si un nouveau est fourni
        if current_user.profile.avatar_url and current_user.profile.avatar_url != profile_update.avatar_url:
            delete_old_file(current_user.profile.avatar_url)
        current_user.profile.avatar_url = profile_update.avatar_url
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.patch("/me/personal", response_model=UserOut)
def update_user_personal_info(
    personal_update: UserPersonalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's personal info (name, email)"""
    
    # Check if email already exists
    if personal_update.email and personal_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == personal_update.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = personal_update.email
    
    if personal_update.full_name:
        current_user.full_name = personal_update.full_name
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/me/profile", response_model=Optional[ProfileOut])
def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get the detailed profile of the current user"""
    return current_user.profile