from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_db
from app.models.message import Message
from app.models.project import Project, ProjectStatus, Proposal, ProposalStatus
from app.models.user import User, UserRole
from app.schemas.message import MessageOut, MessageSend

router = APIRouter()


def ensure_chat_access(db: Session, project_id: int, user_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Autoriser l'accès au chat si le projet est OPEN, ASSIGNED, COMPLETED, etc.
    # Pour autoriser le chat pendant les propositions, on ne filtre plus par status=ACCEPTED
    proposal = (
        db.query(Proposal)
        .filter(Proposal.project_id == project_id)
        .first()
    )
    if not proposal:
        raise HTTPException(
            status_code=403,
            detail="Chat is only available if there is at least one proposal",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user and user.role == UserRole.ADMIN:
        return project

    # Autoriser si on est le client ou si on est un freelance qui a fait une proposition
    freelancer_proposals = db.query(Proposal).filter(
        Proposal.project_id == project_id, 
        Proposal.freelance_id == user_id
    ).first()

    if user_id != project.client_id and not freelancer_proposals:
        raise HTTPException(status_code=403, detail="You are not part of this project chat")

    return project


@router.get("/{project_id}/messages", response_model=List[MessageOut])
def get_project_messages(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_chat_access(db, project_id, current_user.id)
    messages = (
        db.query(Message)
        .filter(Message.project_id == project_id)
        .order_by(Message.created_at)
        .all()
    )
    return messages

@router.post("/{project_id}/messages", response_model=MessageOut, status_code=201)
def send_project_message(
    project_id: int,
    message_in: MessageSend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = ensure_chat_access(db, project_id, current_user.id)
    
    receiver_id = project.client_id
    if current_user.id == project.client_id:
        # If client is sending, try to find an accepted proposal
        accepted_proposal = db.query(Proposal).filter(
            Proposal.project_id == project_id,
            Proposal.status == ProposalStatus.ACCEPTED,
        ).first()
        if accepted_proposal:
            receiver_id = accepted_proposal.freelance_id
        else:
            # Fallback to the first proposal if none is accepted yet (for interview)
            first_proposal = db.query(Proposal).filter(Proposal.project_id == project_id).first()
            if first_proposal:
                receiver_id = first_proposal.freelance_id
            else:
                raise HTTPException(status_code=400, detail="No freelancers to message yet")
                
    message = Message(
        project_id=project_id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=message_in.content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.patch("/{project_id}/messages/read")
def mark_project_messages_read(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_chat_access(db, project_id, current_user.id)
    updated = (
        db.query(Message)
        .filter(
            Message.project_id == project_id,
            Message.receiver_id == current_user.id,
            Message.is_read.is_(False),
        )
        .update({"is_read": True})
    )
    db.commit()
    return {"project_id": project_id, "updated_count": updated}
