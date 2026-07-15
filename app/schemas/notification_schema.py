from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class NotificationBase(BaseModel):
    message: str
    is_read: bool = False
    user_id: int


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    message: Optional[str] = None
    is_read: Optional[bool] = None


class NotificationInDBBase(NotificationBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Notification(NotificationInDBBase):
    pass
