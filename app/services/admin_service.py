from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.models.project import Project
from app.models.project import Proposal

def toggle_user_suspension(db: Session, user_id: int, suspend: bool):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_suspended = suspend
    db.commit()
    return user

def delete_project_admin(db: Session, project_id: int):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}

def get_platform_stats(db: Session):
    total_users = db.query(User).count()
    total_projects = db.query(Project).count()
    total_proposals = db.query(Proposal).count()
    return {
        "total_users": total_users,
        "total_projects": total_projects,
        "total_proposals": total_proposals
    }
