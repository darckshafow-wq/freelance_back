from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.project import Project, ProjectStatus, Proposal, ProposalStatus
from app.schemas.project import ProposalCreate
from app.services.notification_service import create_notification

def create_proposal(db: Session, project_id: int, freelance_id: int, proposal_in: ProposalCreate) -> Proposal:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=400, detail="Project is not open for proposals.")
        
    existing = db.query(Proposal).filter(Proposal.project_id == project_id, Proposal.freelance_id == freelance_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already submitted a proposal for this project.")
        
    proposal = Proposal(
        project_id=project_id,
        freelance_id=freelance_id,
        cover_letter=proposal_in.cover_letter,
        estimated_days=proposal_in.estimated_days,
        status=ProposalStatus.PENDING
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    
    # Notify client
    create_notification(db, project.client_id, "New Proposal", f"You received a new proposal for project {project.title}")
    
    return proposal

def accept_proposal(db: Session, proposal_id: int, client_id: int) -> Proposal:
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
        
    project = proposal.project
    if project.client_id != client_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=400, detail="Project is no longer open")
        
    # Accept the proposal
    proposal.status = ProposalStatus.ACCEPTED
    project.status = ProjectStatus.IN_PROGRESS
    
    # Reject all other pending proposals for this project
    other_proposals = db.query(Proposal).filter(
        Proposal.project_id == project.id, 
        Proposal.id != proposal.id
    ).all()
    
    for op in other_proposals:
        op.status = ProposalStatus.REJECTED
        create_notification(db, op.freelance_id, "Proposal Rejected", f"Your proposal for {project.title} was not selected.")
        
    db.commit()
    db.refresh(proposal)
    
    create_notification(db, proposal.freelance_id, "Proposal Accepted!", f"Your proposal for {project.title} has been accepted!")
    
    return proposal

def submit_work(db: Session, project_id: int, freelance_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    accepted_proposal = db.query(Proposal).filter(
        Proposal.project_id == project_id, 
        Proposal.freelance_id == freelance_id,
        Proposal.status == ProposalStatus.ACCEPTED
    ).first()
    
    if not accepted_proposal:
        raise HTTPException(status_code=403, detail="You do not have an accepted proposal for this project")
        
    if project.status != ProjectStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Project is not in progress")
        
    project.status = ProjectStatus.SUBMITTED
    db.commit()
    db.refresh(project)
    
    create_notification(db, project.client_id, "Work Submitted", f"Work for project {project.title} has been submitted by the freelance.")
    return project
