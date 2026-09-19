from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_user
from app.schemas.user import (
    UserCreate, UserOut, 
    EnableTwoFactorRequest, EnableTwoFactorResponse, VerifyTwoFactorRequest, VerifyTwoFactorResponse,
    DisableTwoFactorRequest, PasswordResetRequest, PasswordResetResponse, PasswordResetConfirm, PasswordResetConfirmResponse
)
from app.services.auth_service import register_user, authenticate
from app.core.security import (
    create_access_token, get_password_hash, generate_password_reset_token, 
    generate_totp_secret, get_totp_provisioning_uri, verify_totp, verify_password
)
from app.core.config import settings
from app.models.user import User
import qrcode
from io import BytesIO
import base64

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, user_in)

@router.post("/login")
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.is_suspended or not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive or suspended user")
    
    # If 2FA is enabled, user must verify TOTP code
    if user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA verification required. Use /auth/login-totp endpoint"
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ==================== TWO-FACTOR AUTHENTICATION (OTP) ====================

@router.post("/enable-2fa", response_model=EnableTwoFactorResponse)
def enable_two_factor(
    request: EnableTwoFactorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate TOTP secret and provisioning URI for 2FA setup"""
    if current_user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled for this user")
    
    # Generate new secret
    secret = generate_totp_secret()
    provisioning_uri = get_totp_provisioning_uri(current_user.email, secret)
    
    # Store secret temporarily in database (not yet enabled)
    current_user.totp_secret = secret
    db.add(current_user)
    db.commit()
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for response
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return EnableTwoFactorResponse(
        secret=secret,
        provisioning_uri=f"data:image/png;base64,{qr_code_base64}"
    )

@router.post("/verify-2fa", response_model=VerifyTwoFactorResponse)
def verify_two_factor(
    request: VerifyTwoFactorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify TOTP code and enable 2FA"""
    if current_user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled")
    
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="No 2FA setup in progress. Call /enable-2fa first")
    
    # Verify the TOTP code
    if not verify_totp(current_user.totp_secret, request.token):
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    # Enable 2FA
    current_user.two_factor_enabled = True
    db.add(current_user)
    db.commit()
    
    return VerifyTwoFactorResponse()

@router.post("/disable-2fa")
def disable_two_factor(
    request: DisableTwoFactorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA (requires password verification)"""
    if not current_user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    
    # Verify password
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Disable 2FA
    current_user.two_factor_enabled = False
    current_user.totp_secret = None
    db.add(current_user)
    db.commit()
    
    return {"message": "2FA disabled successfully"}

@router.post("/login-totp")
def login_with_totp(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """Login with email, password and TOTP code"""
    email = request_data.get("username")
    password = request_data.get("password")
    totp_code = request_data.get("totp_code")
    
    if not all([email, password, totp_code]):
        raise HTTPException(status_code=400, detail="Missing username, password, or totp_code")
    
    user = authenticate(db, email=email, password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if user.is_suspended or not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive or suspended user")
    
    if not user.two_factor_enabled:
        raise HTTPException(status_code=400, detail="2FA not enabled for this user")
    
    # Verify TOTP code
    if not verify_totp(user.totp_secret, totp_code):
        raise HTTPException(status_code=401, detail="Invalid TOTP code")
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ==================== PASSWORD RESET ====================

@router.post("/password-reset-request", response_model=PasswordResetResponse)
def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset - sends token via email (for now just generates)"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # For security, don't reveal if email exists
        return PasswordResetResponse(
            message="If this email exists, a password reset link has been sent"
        )
    
    # Generate reset token (valid for 1 hour)
    reset_token = generate_password_reset_token()
    user.password_reset_token = reset_token
    user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
    db.add(user)
    db.commit()
    
    # In production, send email with reset link:
    # reset_url = f"http://frontend.com/reset-password?token={reset_token}"
    # send_email(user.email, "Password Reset", reset_url)
    
    # For testing, return token
    return PasswordResetResponse(
        message=f"Password reset token: {reset_token} (expires in 1 hour)"
    )

@router.post("/password-reset-confirm", response_model=PasswordResetConfirmResponse)
def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token and new password"""
    user = db.query(User).filter(User.password_reset_token == request.token).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token has expired
    if user.password_reset_expires_at < datetime.utcnow():
        user.password_reset_token = None
        user.password_reset_expires_at = None
        db.add(user)
        db.commit()
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    user.failed_login_attempts = 0  # Reset failed attempts
    db.add(user)
    db.commit()
    
    return PasswordResetConfirmResponse()

