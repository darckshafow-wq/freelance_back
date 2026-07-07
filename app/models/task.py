import enum
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    EXECUTED = "executed"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    description = Column(String(2000), nullable=True)
    price = Column(Float, nullable=False)
    location = Column(String(255), index=True, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    client_id = Column(Integer, ForeignKey("users.id"))
    client = relationship("User", backref="tasks")
