from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.message import Message

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_statistics(db: Session = Depends(get_db)) -> Any:
    """
    Get numerical statistics and percentages.
    """
    # 1. Numerical Statistics
    total_tasks = db.query(func.count(Task.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_freelancers = db.query(func.count(User.id)).filter(User.is_freelancer == True).scalar() or 0
    total_clients = db.query(func.count(User.id)).filter(User.is_client == True).scalar() or 0
    total_admins = db.query(func.count(User.id)).filter(User.is_admin == True).scalar() or 0
    
    validated_tasks = db.query(func.count(Task.id)).filter(Task.status == TaskStatus.VALIDATED).scalar() or 0
    tasks_with_applications = db.query(func.count(func.distinct(Application.task_id))).scalar() or 0
    
    total_messages = db.query(func.count(Message.id)).scalar() or 0
    pending_applications = db.query(func.count(Application.id)).filter(Application.status == ApplicationStatus.PENDING).scalar() or 0
    
    # 2. Percentages
    # Registration breakdown
    freelancer_percentage = (total_freelancers / total_users * 100) if total_users > 0 else 0
    client_percentage = (total_clients / total_users * 100) if total_users > 0 else 0
    
    # Task completion/validation
    validated_task_percentage = (validated_tasks / total_tasks * 100) if total_tasks > 0 else 0
    tasks_applied_percentage = (tasks_with_applications / total_tasks * 100) if total_tasks > 0 else 0
    
    # Site activity proxy: users who have either sent a message, posted a task, or applied
    active_users_query = db.query(User.id).join(Message, User.id == Message.sender_id, isouter=True) \
                           .join(Task, User.id == Task.client_id, isouter=True) \
                           .join(Application, User.id == Application.freelance_id, isouter=True) \
                           .filter((Message.id != None) | (Task.id != None) | (Application.id != None))
    active_users = active_users_query.distinct().count()
    site_activity_percentage = (active_users / total_users * 100) if total_users > 0 else 0
    
    # Reviews are implemented in another endpoint, if we had total reviews we could add it here
    
    return {
        "numerical": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "users_by_role": {
                "freelancers": total_freelancers,
                "clients": total_clients,
                "admins": total_admins
            },
            "validated_tasks": validated_tasks,
            "tasks_applied_to": tasks_with_applications,
            "total_messages": total_messages,
            "pending_applications": pending_applications
        },
        "percentages": {
            "site_activity": round(site_activity_percentage, 2),
            "registration": {
                "freelancers": round(freelancer_percentage, 2),
                "clients": round(client_percentage, 2)
            },
            "tasks": {
                "validated": round(validated_task_percentage, 2),
                "applied": round(tasks_applied_percentage, 2)
            }
        }
    }

@router.get("/freelancer/{user_id}")
def get_freelancer_statistics(user_id: int, db: Session = Depends(get_db)) -> Any:
    """
    Get statistics for a specific freelancer:
    - tasks_completed: number of tasks where this freelancer is assigned and status = executed
    - applications_sent: total applications sent
    - applications_accepted: accepted applications
    - applications_rejected: rejected applications
    - success_rate: percentage of accepted / total sent
    """
    from app.models.application import ApplicationStatus as AppStatus
    
    # Total applications sent by this freelancer
    applications_sent = db.query(func.count(Application.id)).filter(
        Application.freelance_id == user_id
    ).scalar() or 0
    
    # Accepted applications
    applications_accepted = db.query(func.count(Application.id)).filter(
        Application.freelance_id == user_id,
        Application.status == AppStatus.ACCEPTED
    ).scalar() or 0
    
    # Rejected applications
    applications_rejected = db.query(func.count(Application.id)).filter(
        Application.freelance_id == user_id,
        Application.status == AppStatus.REJECTED
    ).scalar() or 0
    
    # Tasks completed (assigned to this freelancer + status executed)
    tasks_completed = db.query(func.count(Task.id)).filter(
        Task.assigned_to_id == user_id,
        Task.status == TaskStatus.EXECUTED
    ).scalar() or 0
    
    # Tasks in progress (assigned to this freelancer + status validated)
    tasks_in_progress = db.query(func.count(Task.id)).filter(
        Task.assigned_to_id == user_id,
        Task.status == TaskStatus.VALIDATED
    ).scalar() or 0
    
    # Success rate
    success_rate = (applications_accepted / applications_sent * 100) if applications_sent > 0 else 0
    
    return {
        "tasks_completed": tasks_completed,
        "tasks_in_progress": tasks_in_progress,
        "applications_sent": applications_sent,
        "applications_accepted": applications_accepted,
        "applications_rejected": applications_rejected,
        "success_rate": round(success_rate, 1),
    }
