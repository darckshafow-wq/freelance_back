from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean(), default=True)
    is_admin = Column(Boolean(), default=False)
    is_client = Column(Boolean(), default=False)
    is_freelancer = Column(Boolean(), default=False)
    location = Column(String(255), nullable=True)
    is_verified = Column(Boolean(), default=False)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(String(255), nullable=True) # Using String for simplicity or DateTime if imported
    refresh_token = Column(String(512), nullable=True)
    refresh_token_expires_at = Column(String(255), nullable=True)
