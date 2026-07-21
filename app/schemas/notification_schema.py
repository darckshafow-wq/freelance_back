from typing import Optional
from pydantic import BaseModel
# Remplace l'ancien import par celui-ci avec un alias 'as' :
from app.models.notifications import Notification as NotificationModel

class NotificationBase(BaseModel):
    message: str
    is_read: Optional[bool] = False

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationUpdate(NotificationBase):
    is_read: Optional[bool] = None 

class NotificationInDBBase(NotificationBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class Notification(NotificationInDBBase):
    pass