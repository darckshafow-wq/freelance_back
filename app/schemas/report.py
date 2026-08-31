from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportBase(BaseModel):
    reason: str
    target_id: Optional[int] = None
    project_id: Optional[int] = None

class ReportCreate(ReportBase):
    pass

class ReportOut(ReportBase):
    id: int
    reporter_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
