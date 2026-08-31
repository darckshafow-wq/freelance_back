from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.project import Project, ProjectStatus, Proposal, ProposalStatus
from app.models.user import User
from app.schemas.project import ProjectCreate
from app.services.notification_service import create_notification

def create_project(db: Session, client_id: int, project_in: ProjectCreate) -> Project:
    project = Project(
        client_id=client_id,
        title=project_in.title,
        description=project_in.description,
        category=project_in.category,
        status=ProjectStatus.OPEN
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def cancel_project(db: Session, project_id: int, user_id: int, is_admin: bool = False) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not is_admin and project.client_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this project")
        
    if project.status not in [ProjectStatus.OPEN, ProjectStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="Can only cancel OPEN or IN_PROGRESS projects")
        
    project.status = ProjectStatus.CANCELLED
    db.commit()
    db.refresh(project)
    return project

def validate_submission(db: Session, project_id: int, client_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.client_id != client_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if project.status != ProjectStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Project must be SUBMITTED to validate")
        
    project.status = ProjectStatus.COMPLETED
    db.commit()
    db.refresh(project)

    # Find the accepted proposal to notify the freelance
    accepted_proposal = db.query(Proposal).filter(
        Proposal.project_id == project.id, 
        Proposal.status == ProposalStatus.ACCEPTED
    ).first()
    if accepted_proposal:
        create_notification(db, accepted_proposal.freelance_id, "Mission Validated", f"Your work on project {project.title} has been validated.")
        
    return project
