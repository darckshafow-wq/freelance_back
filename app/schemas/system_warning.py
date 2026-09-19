from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SystemWarningBase(BaseModel):
    warning_type: str
    description: str

class SystemWarningCreate(SystemWarningBase):
    user_id: Optional[int] = None

class SystemWarningOut(SystemWarningBase):
    id: int
    user_id: Optional[int] = None
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True
