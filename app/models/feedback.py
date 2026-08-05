from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.db.base_class import Base

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(20), nullable=False, default="GENERAL") # BUG, FEATURE_REQUEST, OTHER, GENERAL
    status = Column(String(20), nullable=False, default="PENDING")   # PENDING, ANSWERED, CLOSED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    admin_reply = Column(Text, nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    replied_by = Column(Integer, ForeignKey("users.id"), nullable=True)
