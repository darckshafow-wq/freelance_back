from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.user import User
from app.models.task import Task
from app.models.application import Application

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/stats", response_model=Dict[str, Any])
def get_dashboard_stats(db: Session = Depends(get_db)) -> Any:
    """
    Get generic statistics for the dashboard.
    """
    total_users = db.query(func.count(User.id)).scalar()
    total_freelancers = db.query(func.count(User.id)).filter(User.is_freelancer == True).scalar()
    total_clients = db.query(func.count(User.id)).filter(User.is_client == True).scalar()
    
    total_tasks = db.query(func.count(Task.id)).scalar()
    pending_tasks = db.query(func.count(Task.id)).filter(Task.status == "pending").scalar()
    validated_tasks = db.query(func.count(Task.id)).filter(Task.status == "validated").scalar()
    
    total_applications = db.query(func.count(Application.id)).scalar()

    return {
        "users": {
            "total": total_users,
            "freelancers": total_freelancers,
            "clients": total_clients
        },
        "tasks": {
            "total": total_tasks,
            "pending": pending_tasks,
            "validated": validated_tasks
        },
        "applications": {
            "total": total_applications
        }
    }
