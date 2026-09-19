from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime
from app.models.user import User, Profile, UserRole
from app.models.project import Project, Proposal, ProjectStatus
from app.models.category import Category
from app.models.feedback import Feedback
from app.models.audit import AuditLog
from app.models.system_warning import SystemWarning
from app.models.notification import Notification
from app.models.report import Report, ReportStatus
from app.schemas.feedback import FeedbackReply

# USER MANAGEMENT

def toggle_user_suspension(db: Session, user_id: int, suspend: bool):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_suspended = suspend
    db.commit()
    
    # Log action
    log = AuditLog(
        user_id=None,  # System action
        action="SUSPEND" if suspend else "ACTIVATE",
        target_type="USER",
        target_id=user_id,
        details=f"User {'suspended' if suspend else 'activated'}"
    )
    db.add(log)
    db.commit()
    
    return user

def verify_user_identity(db: Session, user_id: int) -> Profile:
    """Verify freelancer identity"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile.identity_verified = True
    db.commit()
    
    # Log action
    log = AuditLog(
        user_id=None,
        action="VERIFY_IDENTITY",
        target_type="PROFILE",
        target_id=profile.id,
        details=f"Identity verified for user {user.email}"
    )
    db.add(log)
    db.commit()
    
    return profile

# PROJECT MANAGEMENT

def delete_project_admin(db: Session, project_id: int):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    
    # Log action
    log = AuditLog(
        user_id=None,
        action="DELETE_PROJECT",
        target_type="PROJECT",
        target_id=project_id,
        details=f"Project deleted: {project.title}"
    )
    db.add(log)
    db.commit()
    
    return {"message": "Project deleted successfully"}

def get_platform_stats(db: Session):
    total_users = db.query(User).count()
    total_freelancers = db.query(User).filter(User.role == UserRole.FREELANCE).count()
    total_clients = db.query(User).filter(User.role == UserRole.CLIENT).count()
    total_projects = db.query(Project).count()
    total_proposals = db.query(Proposal).count()
    suspended_users = db.query(User).filter(User.is_suspended == True).count()
    status_counts = {
        status.value: db.query(Project).filter(Project.status == status).count()
        for status in ProjectStatus
    }
    
    return {
        "total_users": total_users,
        "total_freelancers": total_freelancers,
        "total_clients": total_clients,
        "total_projects": total_projects,
        "total_proposals": total_proposals,
        "suspended_users": suspended_users,
        "status_breakdown": status_counts,
        "completed_projects": status_counts.get("COMPLETED", 0),
        "pending_projects": status_counts.get("OPEN", 0) + status_counts.get("IN_PROGRESS", 0)
    }


def get_admin_overview(db: Session):
    # Optimisation : On récupère tous les comptes par statut en une seule requête SQL
    status_counts_raw = (
        db.query(Project.status, func.count(Project.id))
        .group_by(Project.status)
        .all()
    )
    status_counts = {s.value: c for s, c in status_counts_raw}
    # S'assurer que tous les statuts sont présents
    for status in ProjectStatus:
        if status.value not in status_counts:
            status_counts[status.value] = 0

    total_clients = db.query(User).filter(User.role == UserRole.CLIENT).count()
    total_freelancers = db.query(User).filter(User.role == UserRole.FREELANCE).count()
    total_projects = sum(status_counts.values())
    total_completed = status_counts.get(ProjectStatus.COMPLETED.value, 0)
    total_open = status_counts.get(ProjectStatus.OPEN.value, 0)
    total_in_progress = status_counts.get(ProjectStatus.IN_PROGRESS.value, 0)

    recent_projects = (
        db.query(Project)
        .order_by(desc(Project.created_at))
        .limit(5)
        .all()
    )
    recent_users = (
        db.query(User)
        .order_by(desc(User.created_at))
        .limit(6)
        .all()
    )

    return {
        "metrics": {
            "clients": total_clients,
            "freelancers": total_freelancers,
            "total_tasks": total_projects,
            "active_users": db.query(User).filter(User.is_active == True, User.is_suspended == False).count(),
            "completed": total_completed,
            "pending": total_open + total_in_progress,
            "completion_rate": round((total_completed / total_projects * 100), 2) if total_projects else 0,
        },
        "status_breakdown": status_counts,
        "recent_projects": [
            {
                "id": project.id,
                "title": project.title,
                "status": project.status.value,
                "client_id": project.client_id,
                "category_id": project.category_id,
                "created_at": project.created_at.isoformat() if project.created_at else None,
            }
            for project in recent_projects
        ],
        "recent_users": [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_suspended": user.is_suspended,
            }
            for user in recent_users
        ],
    }


def get_admin_users(db: Session, skip: int = 0, limit: int = 50, q: Optional[str] = None, role: Optional[str] = None, active: Optional[bool] = None, suspended: Optional[bool] = None):
    query = db.query(User)

    if q:
        search = f"%{q}%"
        query = query.filter(or_(User.email.ilike(search), User.full_name.ilike(search)))
    if role:
        query = query.filter(User.role == role)
    if active is not None:
        query = query.filter(User.is_active == active)
    if suspended is not None:
        query = query.filter(User.is_suspended == suspended)

    return query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()


def get_admin_projects(db: Session, skip: int = 0, limit: int = 50, status: Optional[str] = None, category_id: Optional[int] = None):
    # Optimisation : Utilisation d'une sous-requête pour le comptage des propositions sans charger les objets
    proposal_counts = (
        db.query(Proposal.project_id, func.count(Proposal.id).label("count"))
        .group_by(Proposal.project_id)
        .subquery()
    )

    query = (
        db.query(Project, proposal_counts.c.count)
        .outerjoin(proposal_counts, Project.id == proposal_counts.c.project_id)
        .options(joinedload(Project.category))
    )

    if status:
        query = query.filter(Project.status == status)
    if category_id is not None:
        query = query.filter(Project.category_id == category_id)

    results = query.order_by(desc(Project.created_at)).offset(skip).limit(limit).all()

    projects = []
    for project, count in results:
        project.proposals_count = count or 0
        project.proposals = [] # Évite le chargement différé inutile
        projects.append(project)

    return projects


def get_admin_reports(db: Session, skip: int = 0, limit: int = 50, status: Optional[str] = None):
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)

    return query.order_by(desc(Report.created_at)).offset(skip).limit(limit).all()


def resolve_report_admin(db: Session, report_id: int, status: str = "RESOLVED"):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if status not in {ReportStatus.OPEN.value, ReportStatus.RESOLVED.value}:
        raise HTTPException(status_code=400, detail="Invalid report status")

    report.status = ReportStatus(status)
    db.commit()
    db.refresh(report)

    return report

# AUDIT & SECURITY

def get_audit_logs(db: Session, skip: int = 0, limit: int = 50, action: Optional[str] = None, user_id: Optional[int] = None) -> List[AuditLog]:
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

def get_system_warnings(db: Session, skip: int = 0, limit: int = 50, resolved: Optional[bool] = None) -> List[SystemWarning]:
    query = db.query(SystemWarning)
    
    if resolved is not None:
        query = query.filter(SystemWarning.is_resolved == resolved)
    
    return query.order_by(desc(SystemWarning.created_at)).offset(skip).limit(limit).all()

def resolve_system_warning(db: Session, warning_id: int) -> SystemWarning:
    warning = db.query(SystemWarning).filter(SystemWarning.id == warning_id).first()
    if not warning:
        raise HTTPException(status_code=404, detail="Warning not found")
    
    warning.is_resolved = True
    db.commit()
    
    # Log action
    log = AuditLog(
        user_id=None,
        action="RESOLVE_WARNING",
        target_type="SYSTEM_WARNING",
        target_id=warning_id,
        details=f"Warning resolved: {warning.warning_type}"
    )
    db.add(log)
    db.commit()
    
    return warning

# FEEDBACK MANAGEMENT

def get_pending_feedbacks(db: Session, skip: int = 0, limit: int = 50) -> List[Feedback]:
    return db.query(Feedback).filter(
        Feedback.status == "PENDING"
    ).order_by(desc(Feedback.created_at)).offset(skip).limit(limit).all()

def reply_to_feedback(db: Session, feedback_id: int, reply: FeedbackReply) -> Feedback:
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback.admin_reply = reply.reply
    feedback.status = "REPLIED"
    db.commit()
    
    # Notify user
    notification = Notification(
        user_id=feedback.user_id,
        title="Feedback Reply",
        content=f"Your feedback has been replied to: {reply.reply}",
        is_read=False
    )
    db.add(notification)
    db.commit()
    
    # Log action
    log = AuditLog(
        user_id=None,
        action="REPLY_FEEDBACK",
        target_type="FEEDBACK",
        target_id=feedback_id,
        details=f"Replied to feedback from user {feedback.user_id}"
    )
    db.add(log)
    db.commit()
    
    return feedback

# CATEGORY MANAGEMENT

def create_category(db: Session, name: str) -> Category:
    existing = db.query(Category).filter(Category.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category = Category(name=name, is_active=True)
    db.add(category)
    db.commit()
    db.refresh(category)
    
    # Log action
    log = AuditLog(
        user_id=None,
        action="CREATE_CATEGORY",
        target_type="CATEGORY",
        target_id=category.id,
        details=f"Category created: {name}"
    )
    db.add(log)
    db.commit()
    
    return category

def get_categories(db: Session, active_only: bool = True) -> List[Category]:
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    return query.all()

def update_category(db: Session, category_id: int, name: Optional[str] = None, is_active: Optional[bool] = None) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if name:
        category.name = name
    if is_active is not None:
        category.is_active = is_active
    
    db.commit()
    db.refresh(category)
    
    # Log action
    log = AuditLog(
        user_id=None,
        action="UPDATE_CATEGORY",
        target_type="CATEGORY",
        target_id=category_id,
        details=f"Category updated: {category.name}"
    )
    db.add(log)
    db.commit()
    
    return category

# BROADCAST

def broadcast_notification(db: Session, title: str, content: str, target_role: Optional[str] = None) -> dict:
    """Send notification to all users or specific role"""
    query = db.query(User)
    
    if target_role:
        query = query.filter(User.role == target_role)
    
    users = query.all()
    count = 0
    
    for user in users:
        notification = Notification(
            user_id=user.id,
            title=title,
            content=content,
            is_read=False
        )
        db.add(notification)
        count += 1
    
    db.commit()
    
    # Log action
    log = AuditLog(
        user_id=None,
        action="BROADCAST",
        target_type="NOTIFICATION",
        target_id=None,
        details=f"Broadcast to {count} users (role: {target_role or 'ALL'})"
    )
    db.add(log)
    db.commit()
    
    return {"message": f"Notification sent to {count} users", "count": count}

