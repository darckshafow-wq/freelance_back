from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.task import TaskStatus

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    location: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    title: Optional[str] = None
    price: Optional[float] = None
    status: Optional[TaskStatus] = None

class TaskInDBBase(TaskBase):
    id: int
    client_id: int
    status: TaskStatus
    model_config = ConfigDict(from_attributes=True)

class Task(TaskInDBBase):
    pass
