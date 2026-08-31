from pydantic import BaseModel
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    is_active: Optional[bool] = True

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int

    class Config:
        from_attributes = True
