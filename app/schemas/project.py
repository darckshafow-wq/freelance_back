from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.project import ProjectStatus, ProposalStatus
from app.schemas.user import UserOut
from app.schemas.category import CategoryOut
from app.schemas.location import CountryOut, CityOut, DistrictOut

class ProposalBase(BaseModel):
    message: Optional[str] = None
    proposed_price: float

class ProposalCreate(ProposalBase):
    pass

class DirectOfferCreate(BaseModel):
    freelance_id: int
    message: Optional[str] = None
    proposed_price: float

class ProposalOut(ProposalBase):
    id: int
    project_id: int
    freelance_id: int
    status: ProposalStatus
    is_direct_offer: bool = False
    offered_by_client: bool = False
    created_at: datetime
    responded_at: Optional[datetime] = None
    freelance: Optional[UserOut] = None

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    title: str
    description: str
    country_id: Optional[int] = None
    city_id: Optional[int] = None
    district_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    budget: Optional[float] = None
    scheduled_at: datetime
    category_id: Optional[int] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    client_id: int
    status: ProjectStatus
    created_at: datetime
    finished_at: Optional[datetime] = None
    client: Optional[UserOut] = None
    category: Optional[CategoryOut] = None
    country: Optional[CountryOut] = None
    city: Optional[CityOut] = None
    district: Optional[DistrictOut] = None
    proposals: List[ProposalOut] = []
    proposals_count: int = 0

    class Config:
        from_attributes = True

class ProposalTimelineOut(BaseModel):
    proposal_id: int
    project_id: int
    freelance_id: int
    application_date: datetime
    scheduled_at: datetime
    finished_at: Optional[datetime] = None
    status: ProposalStatus
