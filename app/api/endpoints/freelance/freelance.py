from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from sqlalchemy import func, or_

from app.api import deps
from app.crud.crud_application import application as crud_app
from app.crud.crud_task import task as crud_task
from app.schemas.application import Application, ApplicationCreate
from app.models.task import TaskStatus, Task
from app.models.application import Application as ApplicationModel, ApplicationStatus
from app.models.user import User as UserModel
from app.models.message import Message
from app.models.notifications import Notification as NotificationModel
from app.crud.crud_notification import notification as crud_notification
from app.schemas.notification_schema import Notification as NotificationSchema, NotificationCreate
from app.models.review import Review, ReviewType
from pydantic import BaseModel

# ─── SCHEMAS PYDANTIC POUR LE TRANSIT DES DONNÉES ─────────────────────────

class MessageCreate(BaseModel):
    content: str
    receiver_id: int
    task_id: int | None = None

class MessageResponse(BaseModel):
    id: int
    content: str
    sender_id: int
    receiver_id: int
    task_id: int | None
    timestamp: datetime

    class Config:
        from_attributes = True

class ReviewCreate(BaseModel):
    content: str
    review_type: ReviewType = ReviewType.SUGGESTION

class ReviewResponse(BaseModel):
    id: int
    content: str
    review_type: ReviewType
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

router = APIRouter()


# ─── SECTION 1 : GESTION DES MISSIONS & CANDIDATURES ───────────────────────

@router.get("/tasks", summary="Missions disponibles pour les freelancers")
def get_available_tasks(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    tasks = db.query(Task).filter(Task.status == TaskStatus.VALIDATED).offset(skip).limit(limit).all()
    
    return [{
        "id": task.id,
        "title": task.title,
        "description": task.description or "",
        "price": task.price,
        "client_id": task.client_id,
        "status": task.status.value if task.status else "validated",
    } for task in tasks]


@router.post("/apply", response_model=Application, summary="Postuler à une mission")
def apply_for_task(
    *,
    db: Session = Depends(deps.get_db),
    app_in: ApplicationCreate,
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
) -> Any:
    task = crud_task.get(db, id=app_in.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Mission introuvable")
    if task.status != TaskStatus.VALIDATED:
        raise HTTPException(status_code=400, detail="Vous ne pouvez postuler qu'aux missions validées")

    existing = db.query(ApplicationModel).filter(
        ApplicationModel.task_id == app_in.task_id,
        ApplicationModel.freelance_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Vous avez déjà postulé à cette mission")

    return crud_app.create_with_freelance(db=db, obj_in=app_in, freelance_id=current_user.id)

#TODO: revoire laletre de motivation pour lenvois tu poste 
# FIXME : revoire luniciter de char application mme si il est fais par le meme clien
@router.get("/applications", summary="Mes candidatures")
def get_my_applications(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
    status: Optional[str] = Query(None, description="Filtrer par statut: pending, accepted, rejected"),
) -> Any:
    query = db.query(ApplicationModel).options(joinedload(ApplicationModel.task)).filter(
        ApplicationModel.freelance_id == current_user.id
    )
    if status:
        try:
            status_enum = ApplicationStatus(status.lower())
            query = query.filter(ApplicationModel.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Statut invalide")

    apps = query.all()
    return [{
        "id": app.id,
        "task_id": app.task_id,
        "task_title": app.task.title if app.task else "Mission supprimée",
        "client_id": app.task.client_id if app.task else 0,
        "cover_letter": app.message or "",
        "proposed_budget": app.task.price if app.task else 0,
        "status": app.status.value if app.status else "pending",
        "created_at": None,
    } for app in apps]


# ─── SECTION 2 : DIALOGUES & MESSAGERIE STYLE WHATSAPP ──────────────────────

@router.get("/conversations", summary="Liste des chats actifs (Candidatures acceptées)")
def list_freelance_conversations(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
) -> Any:
    # CORRECTION ICI : Utilisation de la structure imbriquée correcte pour joinedload
    accepted_apps = db.query(ApplicationModel).options(
        joinedload(ApplicationModel.task).options(joinedload(Task.client))
    ).filter(
        ApplicationModel.freelance_id == current_user.id,
        ApplicationModel.status == ApplicationStatus.ACCEPTED
    ).all()

    unique_clients = {}
    for app in accepted_apps:
        if app.task and app.task.client:
            client = app.task.client
            unique_clients[client.id] = {
                "client_id": client.id,
                "client_name": client.full_name or client.email,
                "task_id": app.task_id,
                "task_title": app.task.title
            }

    result = []
    for client_id, client_info in unique_clients.items():
        last_msg = db.query(Message).filter(
            or_(
                (Message.sender_id == current_user.id) & (Message.receiver_id == client_id),
                (Message.sender_id == client_id) & (Message.receiver_id == current_user.id)
            )
        ).order_by(Message.timestamp.desc()).first()

        result.append({
            "contact_id": client_id,
            "contact_name": client_info["client_name"],
            "associated_task_id": client_info["task_id"],
            "associated_task_title": client_info["task_title"],
            "contact_avatar": None,
            "last_message": last_msg.content if last_msg else "Nouvelle discussion ouverte !",
            "last_timestamp": last_msg.timestamp.isoformat() if last_msg else None,
            "unread_count": 0,
        })

    result.sort(key=lambda x: x["last_timestamp"] or "", reverse=True)
    return result


@router.get("/messages/{other_user_id}", response_model=List[MessageResponse], summary="Historique des messages")
def get_conversation(
    other_user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
    skip: int = 0,
    limit: int = 100
) -> Any:
    has_access = db.query(ApplicationModel).join(Task).filter(
        ApplicationModel.freelance_id == current_user.id,
        Task.client_id == other_user_id,
        ApplicationModel.status == ApplicationStatus.ACCEPTED
    ).first()

    if not has_access:
        raise HTTPException(
            status_code=403, 
            detail="Vous n'êtes pas autorisé à ouvrir un chat avec cet utilisateur (aucune mission acceptée)."
        )

    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.desc()).offset(skip).limit(limit).all()

    return messages


@router.post("/messages", response_model=MessageResponse, summary="Envoyer un message")
async def send_freelance_message(
    *,
    db: Session = Depends(deps.get_db),
    msg_in: MessageCreate,
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
) -> Any:
    has_access = db.query(ApplicationModel).join(Task).filter(
        ApplicationModel.freelance_id == current_user.id,
        Task.client_id == msg_in.receiver_id,
        ApplicationModel.status == ApplicationStatus.ACCEPTED
    ).first()

    if not has_access:
        raise HTTPException(status_code=403, detail="Communication refusée. Le client doit d'abord accepter votre offre.")

    db_msg = Message(
        content=msg_in.content,
        sender_id=current_user.id,
        receiver_id=msg_in.receiver_id,
        task_id=msg_in.task_id
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    try:
        from app.websockets.manager import manager
        await manager.send_json_message({
            "type": "new_message",
            "message_id": db_msg.id,
            "sender_id": current_user.id,
            "content": db_msg.content
        }, msg_in.receiver_id)
    except Exception:
        pass

    return db_msg


# ─── SECTION 3 : STATISTIQUES ─────────────────────────────────────────────

@router.get("/stats", summary="Statistiques du freelancer")
def get_freelancer_stats(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
) -> Any:
    # CORRECTION ICI : Utilisation directe des énums importés globalement
    applications_sent = db.query(func.count(ApplicationModel.id)).filter(ApplicationModel.freelance_id == current_user.id).scalar() or 0
    applications_accepted = db.query(func.count(ApplicationModel.id)).filter(ApplicationModel.freelance_id == current_user.id, ApplicationModel.status == ApplicationStatus.ACCEPTED).scalar() or 0
    applications_rejected = db.query(func.count(ApplicationModel.id)).filter(ApplicationModel.freelance_id == current_user.id, ApplicationModel.status == ApplicationStatus.REJECTED).scalar() or 0
    tasks_completed = db.query(func.count(Task.id)).filter(Task.freelancer_id == current_user.id, Task.status == TaskStatus.EXECUTED).scalar() or 0
    tasks_in_progress = db.query(func.count(Task.id)).filter(Task.freelancer_id == current_user.id, Task.status == TaskStatus.VALIDATED).scalar() or 0

    success_rate = (applications_accepted / applications_sent * 100) if applications_sent > 0 else 0

    return {
        "tasks_completed": tasks_completed,
        "tasks_in_progress": tasks_in_progress,
        "applications_sent": applications_sent,
        "applications_accepted": applications_accepted,
        "applications_rejected": applications_rejected,
        "success_rate": round(success_rate, 1),
    }

# ─── SECTION 4 : NOTIFICATIONS ─────────────────────────────────────────────

@router.get("/notifications", response_model=List[NotificationSchema], summary="Mes notifications")
def get_freelancer_notifications(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
) -> Any:
    notifs = (
        db.query(NotificationModel)
        .filter(NotificationModel.user_id == current_user.id)
        .order_by(NotificationModel.created_at.desc())
        .all()
    )
    return notifs

@router.post("/notifications", response_model=NotificationSchema, summary="Créer une notification")
def create_freelancer_notification(
    *,
    db: Session = Depends(deps.get_db),
    message_in: NotificationCreate,
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
) -> Any:
    # Ensure the notification is for the current user
    if message_in.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    notif = crud_notification.create(db, obj_in=message_in)
    return notif

@router.post("/notifications/{notification_id}/read", response_model=NotificationSchema, summary="Marquer comme lue")
def read_freelancer_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
) -> Any:
    db_notification = crud_notification.get(db, id=notification_id)
    if not db_notification or db_notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    return crud_notification.mark_as_read(db, db_obj=db_notification)

@router.delete("/notifications/{notification_id}", summary="Supprimer une notification")
def delete_freelancer_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_freelancer),
) -> Any:
    db_notification = crud_notification.get(db, id=notification_id)
    if not db_notification or db_notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    db.delete(db_notification)
    db.commit()
    return {"deleted": True, "id": notification_id}

# ─── SECTION 5 : AVIS ET SUGGESTIONS ──────────────────────────────────────

@router.post("/reviews", response_model=ReviewResponse, summary="Laisser un avis ou une suggestion")
def create_freelancer_review(
    *,
    db: Session = Depends(deps.get_db),
    review_in: ReviewCreate,
    current_user: UserModel = Depends(deps.get_current_active_freelancer)
) -> Any:
    review = Review(
        content=review_in.content,
        review_type=review_in.review_type,
        user_id=current_user.id
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review