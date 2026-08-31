from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.schemas.user import UserOut

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    project_id: int
    reviewee_id: int

class ReviewOut(ReviewBase):
    id: int
    project_id: int
    reviewer_id: int
    reviewee_id: int
    created_at: datetime
    reviewer: Optional[UserOut] = None

    class Config:
        from_attributes = True
