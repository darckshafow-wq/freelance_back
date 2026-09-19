from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.api.v1.deps import get_db, get_current_freelance
from app.schemas.project import ProposalCreate, ProposalOut, ProjectOut
from app.schemas.stats import FreelanceStatsOut
from app.schemas.report import ReportOut, ReportCreate
from app.schemas.feedback import FeedbackOut, FeedbackCreate
from app.schemas.message import ConversationOut
from app.models.message import Message
from sqlalchemy import func
from datetime import datetime
from app.services.proposal_service import (
    create_proposal, 
    respond_to_direct_offer, 
    cancel_proposal
)
from app.services.task_service import (
    mark_project_arrived, 
    mark_project_finished, 
    get_freelance_stats,
    create_report,
    submit_feedback
)
from app.models.user import User
from app.models.project import Project, ProjectStatus, Proposal, ProposalStatus
from app.models.report import Report
from app.models.feedback import Feedback

router = APIRouter()

@router.get("/projects", response_model=List[ProjectOut])
def list_available_projects(
    skip: int = 0, 
    limit: int = 100, 
    lat: float = None, 
    lng: float = None, 
    radius_km: float = 50.0,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_freelance)
):
    """List all available projects (OPEN status) with optimized counting"""
    # Sous-requête pour compter les propositions efficacement
    proposal_counts = (
        db.query(Proposal.project_id, func.count(Proposal.id).label("count"))
        .group_by(Proposal.project_id)
        .subquery()
    )

    query = (
        db.query(Project, proposal_counts.c.count)
        .outerjoin(proposal_counts, Project.id == proposal_counts.c.project_id)
        .options(joinedload(Project.category))
        .filter(Project.status == ProjectStatus.OPEN)
    )
    
    if lat is not None and lng is not None:
        deg_diff = radius_km / 111.0
        query = query.filter(
            Project.latitude.between(lat - deg_diff, lat + deg_diff),
            Project.longitude.between(lng - deg_diff, lng + deg_diff)
        )
        
    results = query.offset(skip).limit(limit).all()

    projects = []
    for project, count in results:
        project.proposals_count = count or 0
        project.proposals = [] # Ne pas charger les propositions dans la liste
        projects.append(project)

    return projects

@router.post("/projects/{project_id}/proposals", response_model=ProposalOut)
def apply_to_project(project_id: int, proposal_in: ProposalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Submit proposal for a project"""
    return create_proposal(db, project_id, current_user.id, proposal_in)

@router.get("/proposals", response_model=List[ProposalOut])
def get_my_proposals(db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Get proposals submitted by the freelancer"""
    return db.query(Proposal).filter(Proposal.freelance_id == current_user.id).all()

@router.post("/proposals/{proposal_id}/cancel", response_model=ProposalOut)
def cancel_my_proposal(proposal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Cancel a pending proposal"""
    return cancel_proposal(db, proposal_id, current_user.id)

# ========================
# DIRECT OFFERS
# ========================

@router.get("/direct-offers", response_model=List[ProposalOut])
def get_direct_offers(db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Get direct offers received"""
    return db.query(Proposal).filter(
        Proposal.freelance_id == current_user.id,
        Proposal.status == ProposalStatus.DIRECT_OFFER
    ).all()

@router.post("/direct-offers/{proposal_id}/accept", response_model=ProposalOut)
def accept_direct_offer(proposal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Accept a direct offer"""
    return respond_to_direct_offer(db, proposal_id, current_user.id, accept=True)

@router.post("/direct-offers/{proposal_id}/reject", response_model=ProposalOut)
def reject_direct_offer(proposal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Reject a direct offer"""
    return respond_to_direct_offer(db, proposal_id, current_user.id, accept=False)

# ========================
# PROJECT EXECUTION
# ========================

@router.post("/projects/{project_id}/arrived", response_model=ProjectOut)
def mark_arrived(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Mark that you have arrived on-site"""
    return mark_project_arrived(db, project_id, current_user.id)

@router.post("/projects/{project_id}/finished", response_model=ProjectOut)
def mark_finished(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Mark that work is completed"""
    return mark_project_finished(db, project_id, current_user.id)

# ========================
# STATS & ANALYTICS
# ========================

@router.get("/stats", response_model=FreelanceStatsOut)
def get_my_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Get freelancer statistics and KPIs"""
    return get_freelance_stats(db, current_user.id)

# ========================
# REPORTS & DISPUTES
# ========================

@router.post("/reports", response_model=ReportOut)
def file_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_freelance)
):
    """File a report/dispute against a client"""
    return create_report(db, current_user.id, report_in.target_id, report_in.project_id, report_in.reason)

@router.get("/reports/filed", response_model=List[ReportOut])
def get_my_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Get reports filed by this freelancer"""
    return db.query(Report).filter(Report.reporter_id == current_user.id).all()




# ========================
# FEEDBACK & SUPPORT
# ========================

@router.post("/feedback", response_model=FeedbackOut)
def submit_feedback_ticket(
    feedback_in: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_freelance)
):
    """Submit feedback/support ticket to admin"""
    return submit_feedback(db, current_user.id, feedback_in.subject, feedback_in.content)

@router.get("/feedback/my-tickets", response_model=List[FeedbackOut])
def get_my_feedback(db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Get my feedback tickets"""
    return db.query(Feedback).filter(Feedback.user_id == current_user.id).all()

@router.get("/conversations", response_model=List[ConversationOut])
def get_freelance_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    """Get list of conversations for this freelancer (Optimized)"""
    # 1. Sous-requête pour le compte des messages non lus
    unread_sub = (
        db.query(Message.project_id, func.count(Message.id).label("count"))
        .filter(Message.receiver_id == current_user.id, Message.is_read == False)
        .group_by(Message.project_id)
        .subquery()
    )

    # 2. Récupérer les projets auxquels le freelance a postulé
    # On fait un join pour tout avoir d'un coup : Projet + Client + UnreadCount
    query = (
        db.query(Project, unread_sub.c.count)
        .join(Proposal, Project.id == Proposal.project_id)
        .outerjoin(unread_sub, Project.id == unread_sub.c.project_id)
        .options(joinedload(Project.client))
        .filter(Proposal.freelance_id == current_user.id)
    )
    
    results = query.all()
    conversations = []

    for project, unread_count in results:
        # Récupérer le dernier message (on garde cette petite requête car elle est indexée)
        last_message = (
            db.query(Message)
            .filter(Message.project_id == project.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        
        conversations.append(ConversationOut(
            project_id=project.id,
            freelance_id=project.client_id,
            freelance=project.client,
            last_message=last_message,
            unread_count=unread_count or 0,
            updated_at=last_message.created_at if last_message else project.created_at
        ))
        
    return sorted(conversations, key=lambda c: c.updated_at, reverse=True)
