from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.schemas.user import UserOut

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    project_id: int
    receiver_id: int

class MessageSend(BaseModel):
    content: str = Field(..., min_length=1)

class MessageOut(MessageBase):
    id: int
    project_id: int
    sender_id: int
    receiver_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    project_id: int
    freelance_id: int
    freelance: UserOut
    last_message: Optional[MessageOut] = None
    unread_count: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
