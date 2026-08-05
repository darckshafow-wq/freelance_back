from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random
from datetime import datetime, timedelta, timezone

from app.crud.crud_user import user as crud_user
from app.api import deps
from app.services.auth_service import auth_service

router = APIRouter()

@router.post("/login/access-token")
async def login_access_token(request: Request, db: Session = Depends(deps.get_db)) -> Any:
    from app.core.security import verify_password

    content_type = request.headers.get("content-type", "")
    username = None
    password = None

    if "application/json" in content_type:
        payload = await request.json()
        username = payload.get("username")
        password = payload.get("password")
    else:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")

    if not username or not password:
        raise HTTPException(status_code=422, detail="username and password are required")

    user = crud_user.get_by_email(db, email=username)
    if not user:
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")

    return auth_service.issue_tokens(db, user)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(deps.get_db)) -> Any:
    tokens = auth_service.refresh(db, payload.refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expiré")
    return tokens

class EmailSchema(BaseModel):
    email: str

class VerifyOTPSchema(BaseModel):
    email: str
    code: str

@router.post("/send-otp")
def send_otp(data: EmailSchema, db: Session = Depends(deps.get_db)):
    user = crud_user.get_by_email(db, email=data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    otp_code = str(random.randint(100000, 999999))
    user.otp_code = otp_code
    # Simple expiration (10 mins) as string for simplicity, or use real datetime
    # We use string here to match the User model otp_expires_at field
    user.otp_expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    
    db.commit()
    
    # ── DEV MODE : afficher l'OTP dans la console du serveur ──────────────────
    print(f"\n{'='*50}")
    print(f"  📧 OTP pour {data.email}")
    print(f"  🔑 Code : {otp_code}")
    print(f"{'='*50}\n")
    # ─────────────────────────────────────────────────────────────────────────
    
    return {"message": "OTP code sent"}

@router.post("/verify-otp")
def verify_otp(data: VerifyOTPSchema, db: Session = Depends(deps.get_db)):
    user = crud_user.get_by_email(db, email=data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.otp_code or user.otp_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
        
    if user.otp_expires_at:
        expires = datetime.fromisoformat(user.otp_expires_at)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=400, detail="OTP code expired")
            
    # Mark as verified
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    
    return {"message": "User verified successfully"}
