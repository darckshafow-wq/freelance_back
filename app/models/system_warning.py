from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SystemWarning(Base):
    __tablename__ = "system_warnings"

    id = Column(Integer, primary_key=True, index=True)
    warning_type = Column(String, nullable=False) # e.g. "BRUTE_FORCE", "ANOMALY"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
