from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.project import Project, ProjectStatus, Proposal, ProposalStatus
from app.models.feedback import Feedback
from app.models.user import User
from app.models.report import Report, ReportStatus
from app.models.review import Review
from app.services.notification_service import create_notification
from sqlalchemy import func, and_

def mark_project_arrived(db: Session, project_id: int, freelancer_id: int) -> Project:
    """Freelancer marks project as ARRIVED (on-site)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if freelancer has accepted proposal
    accepted_proposal = db.query(Proposal).filter(
        Proposal.project_id == project_id,
        Proposal.freelance_id == freelancer_id,
        Proposal.status == ProposalStatus.ACCEPTED
    ).first()
    
    if not accepted_proposal:
        raise HTTPException(status_code=403, detail="You do not have an accepted proposal for this project")
    
    if project.status != ProjectStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Project is not in progress")
    
    project.status = ProjectStatus.ARRIVED
    db.commit()
    db.refresh(project)
    
    # Notify client
    create_notification(db, project.client_id, "Freelancer Arrived", f"Freelancer has arrived for project {project.title}")
    
    return project

def mark_project_finished(db: Session, project_id: int, freelancer_id: int) -> Project:
    """Freelancer marks project as FINISHED (work completed)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if freelancer has accepted proposal
    accepted_proposal = db.query(Proposal).filter(
        Proposal.project_id == project_id,
        Proposal.freelance_id == freelancer_id,
        Proposal.status == ProposalStatus.ACCEPTED
    ).first()
    
    if not accepted_proposal:
        raise HTTPException(status_code=403, detail="You do not have an accepted proposal for this project")
    
    if project.status not in [ProjectStatus.IN_PROGRESS, ProjectStatus.ARRIVED]:
        raise HTTPException(status_code=400, detail="Project must be IN_PROGRESS or ARRIVED to mark as finished")
    
    project.status = ProjectStatus.FINISHED
    project.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    # Notify client
    create_notification(db, project.client_id, "Work Completed", f"Freelancer has completed work for project {project.title}. Please validate when ready.")
    
    return project

def submit_feedback(db: Session, user_id: int, subject: str, content: str) -> Feedback:
    """User submits feedback/ticket to admin"""
    feedback = Feedback(
        user_id=user_id,
        subject=subject,
        content=content,
        status="PENDING"
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    # No immediate notification - admin will see in feedback list
    
    return feedback

def get_freelance_stats(db: Session, freelancer_id: int) -> dict:
    """Get statistics for a freelancer"""
    user = db.query(User).filter(User.id == freelancer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Completed projects
    completed = db.query(Project).filter(
        Project.status.in_([ProjectStatus.COMPLETED, ProjectStatus.ARRIVED])
    ).join(Proposal).filter(
        Proposal.freelance_id == freelancer_id,
        Proposal.status == ProposalStatus.ACCEPTED
    ).count()
    
    # Active projects
    active = db.query(Project).filter(
        Project.status.in_([ProjectStatus.IN_PROGRESS])
    ).join(Proposal).filter(
        Proposal.freelance_id == freelancer_id,
        Proposal.status == ProposalStatus.ACCEPTED
    ).count()
    
    # Pending proposals
    pending = db.query(Proposal).filter(
        Proposal.freelance_id == freelancer_id,
        Proposal.status == ProposalStatus.PENDING
    ).count()
    
    # Average rating and total reviews
    reviews = db.query(Review).filter(Review.reviewee_id == freelancer_id).all()
    total_reviews = len(reviews)
    average_rating = sum([r.rating for r in reviews]) / total_reviews if total_reviews > 0 else 0.0
    
    # Cancellation rate (proposals rejected or disputes)
    rejected = db.query(Proposal).filter(
        Proposal.freelance_id == freelancer_id,
        Proposal.status == ProposalStatus.REJECTED
    ).count()
    
    total_proposals = db.query(Proposal).filter(
        Proposal.freelance_id == freelancer_id
    ).count()
    
    cancellation_rate = rejected / total_proposals if total_proposals > 0 else 0.0
    
    return {
        "completed_projects": completed,
        "active_projects": active,
        "pending_proposals": pending,
        "average_rating": round(average_rating, 2),
        "total_reviews": total_reviews,
        "cancellation_rate": round(cancellation_rate, 2)
    }

def get_client_stats(db: Session, client_id: int) -> dict:
    """Get statistics for a client"""
    user = db.query(User).filter(User.id == client_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Total projects
    total = db.query(Project).filter(Project.client_id == client_id).count()
    
    # Completed projects
    completed = db.query(Project).filter(
        Project.client_id == client_id,
        Project.status == ProjectStatus.COMPLETED
    ).count()
    
    # Active projects
    active = db.query(Project).filter(
        Project.client_id == client_id,
        Project.status.in_([ProjectStatus.IN_PROGRESS, ProjectStatus.ARRIVED, ProjectStatus.FINISHED])
    ).count()
    
    # Disputed projects
    disputes = db.query(Project).filter(
        Project.client_id == client_id,
        Project.status == ProjectStatus.DISPUTED
    ).count()
    
    # Average freelancer rating given by client
    reviews = db.query(Review).filter(Review.reviewer_id == client_id).all()
    total_reviews = len(reviews)
    average_rating = sum([r.rating for r in reviews]) / total_reviews if total_reviews > 0 else 0.0
    
    # Completion rate
    completion_rate = completed / total if total > 0 else 0.0
    
    return {
        "total_projects": total,
        "completed_projects": completed,
        "active_projects": active,
        "average_freelancer_rating": round(average_rating, 2),
        "total_disputes": disputes,
        "completion_rate": round(completion_rate, 2)
    }

def create_report(db: Session, reporter_id: int, target_id: int, project_id: int, reason: str) -> Report:
    """Create a report/dispute"""
    report = Report(
        reporter_id=reporter_id,
        target_id=target_id,
        project_id=project_id,
        reason=reason,
        status=ReportStatus.OPEN
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Notify admin
    create_notification(db, None, "New Report", f"New report filed for project {project_id}: {reason}")
    
    return report
