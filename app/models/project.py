import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ProjectStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ARRIVED = "ARRIVED"
    FINISHED = "FINISHED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"

class ProposalStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    localisation = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    
    status = Column(Enum(ProjectStatus), default=ProjectStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("User", back_populates="projects", foreign_keys=[client_id])
    category = relationship("Category", back_populates="projects")
    proposals = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    freelance_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    message = Column(Text, nullable=True)
    proposed_price = Column(Float, nullable=False)
    
    status = Column(Enum(ProposalStatus), default=ProposalStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="proposals")
    freelance = relationship("User", back_populates="proposals", foreign_keys=[freelance_id])
