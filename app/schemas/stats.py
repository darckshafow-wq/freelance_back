from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FreelanceStatsOut(BaseModel):
    completed_projects: int
    active_projects: int
    pending_proposals: int
    average_rating: float
    total_reviews: int
    cancellation_rate: float

class ClientStatsOut(BaseModel):
    total_projects: int
    completed_projects: int
    active_projects: int
    average_freelancer_rating: float
    total_disputes: int
    completion_rate: float
