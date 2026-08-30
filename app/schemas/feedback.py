from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class FeedbackBase(BaseModel):
    content: str
    category: str = "GENERAL"

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackReply(BaseModel):
    admin_reply: str
    status: str = "ANSWERED"

class Feedback(FeedbackBase):
    id: int
    status: str
    created_at: datetime
    admin_reply: Optional[str] = None
    replied_at: Optional[datetime] = None
    user_id: int
    replied_by: Optional[int] = None

    class Config:
        from_attributes = True
