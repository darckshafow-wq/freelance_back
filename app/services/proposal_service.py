from sqlalchemy.orm import Session
from datetime import datetime
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
        message=proposal_in.message,
        proposed_price=proposal_in.proposed_price,
        status=ProposalStatus.PENDING,
        is_direct_offer=False,
        offered_by_client=False
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    
    # Notify client
    create_notification(db, project.client_id, "New Proposal", f"You received a new proposal for project {project.title}")
    
    return proposal

def create_direct_offer(db: Session, project_id: int, freelance_id: int, client_id: int, message: str, proposed_price: float) -> Proposal:
    """Client creates a direct offer to a specific freelancer"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.client_id != client_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=400, detail="Project is not open")
    
    # Check if freelancer already has a proposal for this project
    existing = db.query(Proposal).filter(
        Proposal.project_id == project_id, 
        Proposal.freelance_id == freelance_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Freelancer already has a proposal for this project")
    
    proposal = Proposal(
        project_id=project_id,
        freelance_id=freelance_id,
        message=message,
        proposed_price=proposed_price,
        status=ProposalStatus.DIRECT_OFFER,
        is_direct_offer=True,
        offered_by_client=True
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    
    # Notify freelancer
    create_notification(db, freelance_id, "Direct Offer Received", f"You received a direct offer for project {project.title}. Price: ${proposed_price}")
    
    return proposal

def respond_to_direct_offer(db: Session, proposal_id: int, freelancer_id: int, accept: bool) -> Proposal:
    """Freelancer accepts or rejects a direct offer"""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    if proposal.freelance_id != freelancer_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if proposal.status != ProposalStatus.DIRECT_OFFER:
        raise HTTPException(status_code=400, detail="This is not a direct offer")
    
    if accept:
        proposal.status = ProposalStatus.ACCEPTED
        proposal.project.status = ProjectStatus.IN_PROGRESS
        create_notification(db, proposal.project.client_id, "Direct Offer Accepted", f"Freelancer accepted your direct offer for {proposal.project.title}")
    else:
        proposal.status = ProposalStatus.REJECTED
        proposal.responded_at = datetime.utcnow()
        create_notification(db, proposal.project.client_id, "Direct Offer Rejected", f"Freelancer declined your direct offer for {proposal.project.title}")
    
    db.commit()
    db.refresh(proposal)
    
    return proposal

def cancel_proposal(db: Session, proposal_id: int, freelancer_id: int) -> Proposal:
    """Freelancer cancels their proposal"""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    if proposal.freelance_id != freelancer_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if proposal.status not in [ProposalStatus.PENDING, ProposalStatus.DIRECT_OFFER]:
        raise HTTPException(status_code=400, detail="Can only cancel pending or direct offer proposals")
    
    proposal.status = ProposalStatus.REJECTED
    proposal.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(proposal)
    
    # Notify client
    create_notification(db, proposal.project.client_id, "Proposal Cancelled", f"Freelancer cancelled their proposal for {proposal.project.title}")
    
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
    proposal.responded_at = datetime.utcnow()
    project.status = ProjectStatus.IN_PROGRESS
    
    # Reject all other pending proposals for this project
    other_proposals = db.query(Proposal).filter(
        Proposal.project_id == project.id, 
        Proposal.id != proposal.id
    ).all()
    
    for op in other_proposals:
        op.status = ProposalStatus.REJECTED
        op.responded_at = datetime.utcnow()
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
        
    project.status = ProjectStatus.FINISHED
    project.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    create_notification(db, project.client_id, "Work Submitted", f"Work for project {project.title} has been submitted by the freelancer.")
    return project
