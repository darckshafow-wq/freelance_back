from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.application import ApplicationStatus

class ApplicationBase(BaseModel):
    message: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    task_id: int

class ApplicationUpdate(BaseModel):
    status: ApplicationStatus

class ApplicationInDBBase(ApplicationBase):
    id: int
    task_id: int
    freelance_id: int
    status: ApplicationStatus
    model_config = ConfigDict(from_attributes=True)

class Application(ApplicationInDBBase):
    pass
