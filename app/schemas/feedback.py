from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FeedbackBase(BaseModel):
    subject: str
    content: str

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackOut(FeedbackBase):
    id: int
    user_id: int
    admin_reply: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class FeedbackReply(BaseModel):
    reply: str

