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

    # Auteur de l'avis
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Destinataire de l'avis (profil évalué — nullable pour les suggestions générales)
    reviewee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    user = relationship("User", foreign_keys=[user_id], backref="reviews_written")
    reviewee = relationship("User", foreign_keys=[reviewee_id], backref="reviews_received")
