import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class ReviewType(str, enum.Enum):
    SUGGESTION = "suggestion"
    IMPROVEMENT = "improvement"
    COMPLAINT = "complaint"

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(2000), nullable=False)
    review_type = Column(Enum(ReviewType), default=ReviewType.SUGGESTION, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", backref="reviews")
