from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.crud.crud_user import user as crud_user
from app.api import deps

router = APIRouter()

@router.post("/login/access-token")
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    from app.core.security import verify_password, create_access_token

    user = crud_user.get_by_email(db, email=form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")
    
    # Validation du mot de passe (à décommenter si les mots de passe de test sont hashés, sinon laisser pour test ou utiliser un mot de passe standard "string")
    if not verify_password(form_data.password, user.hashed_password):
        # Pour éviter de bloquer avec les comptes de test (qui n'ont pas de mdp hashé),
        # si le hash correspond directement (cas du mock) ou autre, on laisse passer pour le dev,
        # mais on devrait utiliser :
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")

    access_token = create_access_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_verified": user.is_verified,
    }

from pydantic import BaseModel
import random
from datetime import datetime, timedelta

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
    user.otp_expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    
    db.commit()
    
    # Simulate sending email
    print(f"\\n\\n{'='*40}\\n[SIMULATED EMAIL] OTP Code for {data.email}: {otp_code}\\n{'='*40}\\n\\n")
    
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
        if datetime.utcnow() > expires:
            raise HTTPException(status_code=400, detail="OTP code expired")
            
    # Mark as verified
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    
    return {"message": "User verified successfully"}
