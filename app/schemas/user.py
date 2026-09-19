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

# Two-Factor Authentication (OTP) Schemas
class EnableTwoFactorRequest(BaseModel):
    """Request to enable 2FA"""
    pass

class EnableTwoFactorResponse(BaseModel):
    """Response with QR code provisioning URI"""
    secret: str
    provisioning_uri: str
    message: str = "Scan the QR code with Google Authenticator or Authy. Then verify with the 6-digit code."

class VerifyTwoFactorRequest(BaseModel):
    """Request to verify OTP code and enable 2FA"""
    token: str  # 6-digit code from authenticator

class VerifyTwoFactorResponse(BaseModel):
    """Response after successful 2FA verification"""
    message: str = "Two-factor authentication enabled successfully"
    two_factor_enabled: bool = True

class DisableTwoFactorRequest(BaseModel):
    """Request to disable 2FA"""
    password: str  # User must verify password to disable 2FA

class LoginWithTOTPRequest(BaseModel):
    """Login request with TOTP code"""
    username: str
    password: str
    totp_code: str

# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    """Request password reset"""
    email: EmailStr

class PasswordResetResponse(BaseModel):
    """Response after reset token sent"""
    message: str = "Password reset link sent to email"

class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token and new password"""
    token: str
    new_password: str

class PasswordResetConfirmResponse(BaseModel):
    """Response after password successfully reset"""
    message: str = "Password reset successfully. Please login with your new password."

