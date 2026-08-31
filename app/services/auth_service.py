from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, Profile, UserRole
from app.models.system_warning import SystemWarning
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token
from datetime import datetime

MAX_LOGIN_ATTEMPTS = 10

def register_user(db: Session, user_in: UserCreate) -> User:
    if user_in.role == UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot register as ADMIN directly.")
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = Profile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user

def authenticate(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
        
    if not verify_password(password, user.hashed_password):
        user.failed_login_attempts += 1
        user.last_failed_login = datetime.utcnow()
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.is_suspended = True
            warning = SystemWarning(
                warning_type="BRUTE_FORCE",
                user_id=user.id,
                description=f"Account suspended after {MAX_LOGIN_ATTEMPTS} failed login attempts."
            )
            db.add(warning)
        db.commit()
        return None
        
    # Reset attempts on success
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        db.commit()
        
    return user
