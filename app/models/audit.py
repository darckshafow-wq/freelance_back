from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from app.db.base_class import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    path = Column(String(1024), nullable=False)
    method = Column(String(10), nullable=False)
    role = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
