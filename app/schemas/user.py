from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.user import UserRole

class ProfileBase(BaseModel):
    bio: Optional[str] = None
    skills: Optional[str] = None
    avatar_url: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileOut(ProfileBase):
    id: int
    user_id: int
    rating_average: float
    identity_verified: bool

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str
    role: UserRole

class UserOut(UserBase):
    id: int
    role: UserRole
    is_active: bool
    is_suspended: bool
    created_at: datetime
    failed_login_attempts: int
    last_failed_login: Optional[datetime] = None
    profile: Optional[ProfileOut] = None

    class Config:
        from_attributes = True
