import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, Float, Boolean
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
    DIRECT_OFFER = "DIRECT_OFFER"
    PENDING_COMPLETION = "PENDING_COMPLETION"

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Colonnes pour la localisation structurée
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    image_url = Column(String, nullable=True)
    budget = Column(Float, nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    
    status = Column(Enum(ProjectStatus), default=ProjectStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("User", back_populates="projects", foreign_keys=[client_id])
    category = relationship("Category", back_populates="projects")
    country = relationship("Country")
    city = relationship("City")
    district = relationship("District")
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
    is_direct_offer = Column(Boolean, default=False, nullable=False)
    offered_by_client = Column(Boolean, default=False, nullable=False)
    
    status = Column(Enum(ProposalStatus), default=ProposalStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="proposals")
    freelance = relationship("User", back_populates="proposals", foreign_keys=[freelance_id])
