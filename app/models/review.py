from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.db.base_class import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Float, nullable=False)
    comment = Column(String(2000), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    reviewer = relationship("User", foreign_keys=[reviewer_id], backref="reviews_given")
    reviewee = relationship("User", foreign_keys=[reviewee_id], backref="reviews_received")
    task = relationship("Task", backref="reviews")

