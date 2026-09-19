from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.api.v1.deps import get_db, get_current_client
from app.schemas.project import ProjectCreate, ProjectOut, ProposalOut, DirectOfferCreate, ProposalTimelineOut
from app.schemas.feedback import FeedbackCreate, FeedbackOut
from app.schemas.stats import ClientStatsOut
from app.schemas.report import ReportOut, ReportCreate
from app.schemas.category import CategoryOut
from app.schemas.user import UserOut
from app.schemas.message import ConversationOut
from app.services.project_service import create_project, cancel_project, validate_submission
from app.services.proposal_service import accept_proposal, create_direct_offer
from app.services.task_service import submit_feedback, get_client_stats, create_report
from app.models.user import User
from app.models.project import Project, Proposal, ProjectStatus, ProposalStatus
from app.models.feedback import Feedback
from app.models.report import Report
from app.models.category import Category
from app.models.message import Message

router = APIRouter()

# ========================
# PROJECT MANAGEMENT
# ========================

@router.post("/projects", response_model=ProjectOut)
def create_new_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Create a new task/project"""
    return create_project(db, current_user.id, project_in)

@router.get("/projects", response_model=List[ProjectOut])
def get_my_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Get all my projects"""
    projects = db.query(Project).options(joinedload(Project.category), joinedload(Project.proposals)).filter(Project.client_id == current_user.id).all()
    for p in projects:
        p.proposals_count = len(p.proposals)
    return projects

@router.get("/public-projects", response_model=List[ProjectOut])
def get_public_projects(
    skip: int = 0, 
    limit: int = 100, 
    lat: float = None, 
    lng: float = None, 
    radius_km: float = 50.0,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_client)
):
    """Get all open projects available to the authenticated client."""
    query = db.query(Project).options(joinedload(Project.category), joinedload(Project.proposals)).filter(Project.status == ProjectStatus.OPEN)
    
    # Rough bounding box filter for SQLite
    if lat is not None and lng is not None:
        deg_diff = radius_km / 111.0
        query = query.filter(
            Project.latitude.between(lat - deg_diff, lat + deg_diff),
            Project.longitude.between(lng - deg_diff, lng + deg_diff)
        )
        
    projects = query.offset(skip).limit(limit).all()
    for p in projects:
        p.proposals_count = len(p.proposals)
    return projects

@router.get("/categories", response_model=List[CategoryOut])
def get_client_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Get active categories available when creating a project."""
    return db.query(Category).filter(Category.is_active.is_(True)).order_by(Category.name).all()

@router.post("/projects/{project_id}/cancel", response_model=ProjectOut)
def cancel_my_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Cancel a project"""
    return cancel_project(db, project_id, current_user.id)

@router.post("/projects/{project_id}/validate", response_model=ProjectOut)
def validate_project_submission(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Validate project completion (mark as COMPLETED)"""
    return validate_submission(db, project_id, current_user.id)

# ========================
# PROPOSAL MANAGEMENT
# ========================

@router.post("/proposals/{proposal_id}/accept", response_model=ProposalOut)
def accept_freelance_proposal(proposal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Accept a freelancer proposal"""
    return accept_proposal(db, proposal_id, current_user.id)

@router.get("/proposals", response_model=List[ProposalOut])
def get_my_proposals(db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Get proposals submitted for the client's projects"""
    return (
        db.query(Proposal)
        .join(Project, Proposal.project_id == Project.id)
        .filter(Project.client_id == current_user.id)
        .all()
    )

@router.get("/proposals/{proposal_id}/freelance-profile", response_model=UserOut)
def get_proposal_freelance_profile(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
):
    proposal = (
        db.query(Proposal)
        .join(Project, Proposal.project_id == Project.id)
        .filter(Proposal.id == proposal_id, Project.client_id == current_user.id)
        .first()
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal.freelance

@router.get("/proposals/{proposal_id}/timeline", response_model=ProposalTimelineOut)
def get_proposal_timeline(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
):
    proposal = (
        db.query(Proposal)
        .join(Project, Proposal.project_id == Project.id)
        .filter(Proposal.id == proposal_id, Project.client_id == current_user.id)
        .first()
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalTimelineOut(
        proposal_id=proposal.id,
        project_id=proposal.project_id,
        freelance_id=proposal.freelance_id,
        application_date=proposal.created_at,
        scheduled_at=proposal.project.scheduled_at,
        finished_at=proposal.project.finished_at,
        status=proposal.status,
    )

# ========================
# DIRECT OFFERS
# ========================

@router.post("/projects/{project_id}/direct-offer", response_model=ProposalOut)
def send_direct_offer(
    project_id: int,
    offer_in: DirectOfferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client)
):
    """Send a direct offer to a specific freelancer"""
    return create_direct_offer(
        db, 
        project_id, 
        offer_in.freelance_id, 
        current_user.id, 
        offer_in.message or "", 
        offer_in.proposed_price
    )

@router.get("/direct-offers/sent", response_model=List[ProposalOut])
def get_sent_direct_offers(db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Get all direct offers sent by this client"""
    return (
        db.query(Proposal)
        .join(Project, Proposal.project_id == Project.id)
        .filter(Project.client_id == current_user.id, Proposal.is_direct_offer == True)
        .all()
    )

# ========================
# STATS & ANALYTICS
# ========================

@router.get("/stats", response_model=ClientStatsOut)
def get_my_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Get client statistics and KPIs"""
    return get_client_stats(db, current_user.id)

# ========================
# FEEDBACK & SUPPORT
# ========================

@router.post("/feedback", response_model=FeedbackOut)
def submit_feedback_ticket(
    feedback_in: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client)
):
    """Submit feedback/support ticket to admin"""
    feedback = submit_feedback(db, current_user.id, feedback_in.subject, feedback_in.content)
    return feedback

@router.get("/feedback/my-tickets", response_model=List[FeedbackOut])
def get_my_feedback(db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Get my feedback tickets"""
    return db.query(Feedback).filter(Feedback.user_id == current_user.id).all()

# ========================
# REPORTS & DISPUTES
# ========================

@router.post("/reports", response_model=ReportOut)
def file_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client)
):
    """File a report/dispute against a freelancer"""
    return create_report(db, current_user.id, report_in.target_id, report_in.project_id, report_in.reason)

@router.get("/reports/filed", response_model=List[ReportOut])
def get_my_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Get reports filed by this client"""
    return db.query(Report).filter(Report.reporter_id == current_user.id).all()

@router.get("/conversations", response_model=List[ConversationOut])
def get_client_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    """Get list of conversations for this client (Optimized)"""
    # Sous-requête pour le compte des messages non lus
    unread_sub = (
        db.query(Message.project_id, func.count(Message.id).label("count"))
        .filter(Message.receiver_id == current_user.id, Message.is_read == False)
        .group_by(Message.project_id)
        .subquery()
    )

    # Récupérer les projets du client qui ont un freelance assigné (proposal acceptée)
    query = (
        db.query(Project, Proposal, unread_sub.c.count)
        .join(Proposal, Project.id == Proposal.project_id)
        .outerjoin(unread_sub, Project.id == unread_sub.c.project_id)
        .options(joinedload(Proposal.freelance))
        .filter(
            Project.client_id == current_user.id,
            Proposal.status == ProposalStatus.ACCEPTED
        )
    )

    results = query.all()
    conversations = []

    for project, proposal, unread_count in results:
        last_message = (
            db.query(Message)
            .filter(Message.project_id == project.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        conversations.append(ConversationOut(
            project_id=project.id,
            freelance_id=proposal.freelance_id,
            freelance=proposal.freelance,
            last_message=last_message,
            unread_count=unread_count or 0,
            updated_at=last_message.created_at if last_message else project.created_at,
        ))
    return sorted(conversations, key=lambda c: c.updated_at, reverse=True)


