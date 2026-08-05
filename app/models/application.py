import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INTERVIEW = "interview"

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String(2000), nullable=True)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING, index=True)
    
    task_id = Column(Integer, ForeignKey("tasks.id"))
    freelance_id = Column(Integer, ForeignKey("users.id"))
    
    task = relationship("Task", backref="applications")
    freelance = relationship("User", backref="applications")
