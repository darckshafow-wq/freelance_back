from pydantic import BaseModel
from typing import Optional

class BroadcastNotification(BaseModel):
    title: str
    content: str
    target_role: Optional[str] = None  # ADMIN, CLIENT, FREELANCE, or None for all
