from datetime import datetime, timedelta
from typing import Optional, Any
import secrets
import string

import bcrypt
from passlib.context import CryptContext
from jose import jwt
from app.core.config import settings
import pyotp

if not hasattr(bcrypt, "__about__"):
    class _CompatAbout:
        __version__ = getattr(bcrypt, "__version__", "unknown")
    bcrypt.__about__ = _CompatAbout()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def generate_password_reset_token() -> str:
    """Generate a secure random token for password reset"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(32))

def generate_totp_secret() -> str:
    """Generate a TOTP secret for Two-Factor Authentication"""
    return pyotp.random_base32()

def get_totp_provisioning_uri(email: str, secret: str, issuer: str = "Freelance API") -> str:
    """Get QR code provisioning URI for TOTP"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)

def verify_totp(secret: str, token: str) -> bool:
    """Verify TOTP token against secret"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token)
