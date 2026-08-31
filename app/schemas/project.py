from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.project import ProjectStatus, ProposalStatus
from app.schemas.user import UserOut

class ProposalBase(BaseModel):
    message: Optional[str] = None
    proposed_price: float

class ProposalCreate(ProposalBase):
    pass

class ProposalOut(ProposalBase):
    id: int
    project_id: int
    freelance_id: int
    status: ProposalStatus
    created_at: datetime
    freelance: Optional[UserOut] = None

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    title: str
    description: str
    localisation: str
    scheduled_at: datetime
    category_id: Optional[int] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    client_id: int
    status: ProjectStatus
    created_at: datetime
    client: Optional[UserOut] = None
    proposals: List[ProposalOut] = []

    class Config:
        from_attributes = True
