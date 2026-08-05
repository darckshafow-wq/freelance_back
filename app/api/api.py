from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.api.endpoints import auth, users
from app.api.endpoints.admin.admin import router as admin_router
from app.api.endpoints.client.client import (
    create_task,
    get_my_tasks,
    router as client_router,
)
from app.api.endpoints.feedback import router as feedback_router
from app.api.endpoints.freelance.freelance import (
    MessageCreate,
    MessageResponse,
    router as freelance_router,
    send_freelance_message,
)
from app.api.endpoints.users import (
    ReviewCreate,
    ReviewResponse,
    create_review,
)
from app.api.endpoints import ws
from app.models.application import Application as ApplicationModel
from app.models.message import Message
from app.models.task import Task as TaskModel
from app.models.user import User as UserModel
from app.schemas.task import Task, TaskCreate

api_router = APIRouter()

# ─── CORE AUTH & UTILISATEURS ──────────────────────────────────────────
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# ─── ESPACE UNIQUE DU FREELANCE ───────────────────────────────────────────
# Expose toutes nos routes optimisées (/tasks, /apply, /conversations, /messages, /stats, etc.)
api_router.include_router(freelance_router, prefix="/freelance", tags=["freelance"])

# ─── AUTRES RÔLES ET WEBSOCKETS ───────────────────────────────────────────
api_router.include_router(client_router, prefix="/client", tags=["client"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(feedback_router, tags=["feedback"])
api_router.include_router(ws.router, prefix="/ws", tags=["websockets"])


# --- Root-level proxies so tests can call /api/v1/... directly ---
@api_router.post("/tasks", response_model=Task, tags=["client"])
def create_task_root(
    *,
    db: Session = Depends(deps.get_db),
    task_in: TaskCreate,
    current_user: UserModel = Depends(deps.get_current_active_client),
) -> Any:
    return create_task(db=db, task_in=task_in, current_user=current_user)


@api_router.get("/tasks", response_model=List[Task], tags=["client"])
def get_my_tasks_root(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_client),
) -> Any:
    return get_my_tasks(db=db, current_user=current_user)


@api_router.get("/messages/", tags=["messages"])
def get_conversations_root(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    """Retourne la liste des conversations (derniers messages par contact) de l'utilisateur."""
    from sqlalchemy import or_, desc
    from app.models.user import User as UserModel2

    # Récupère tous les messages impliquant l'utilisateur
    messages = (
        db.query(Message)
        .filter(
            or_(
                Message.sender_id == current_user.id,
                Message.receiver_id == current_user.id,
            )
        )
        .order_by(desc(Message.id))
        .all()
    )

    # Construit la liste des contacts uniques avec le dernier message
    seen_contacts = set()
    conversations = []
    for msg in messages:
        other_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        if other_id not in seen_contacts:
            seen_contacts.add(other_id)
            other_user = db.query(UserModel2).filter(UserModel2.id == other_id).first()
            conversations.append({
                "contact_id": other_id,
                "contact_name": other_user.full_name if other_user else "Inconnu",
                "last_message": msg.content,
                "task_id": msg.task_id,
            })

    return conversations


@api_router.post("/messages/", response_model=MessageResponse, tags=["messages"])
def send_message_root(
    *,
    db: Session = Depends(deps.get_db),
    msg_in: MessageCreate,
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    db_msg = Message(
        content=msg_in.content,
        sender_id=current_user.id,
        receiver_id=msg_in.receiver_id,
        task_id=getattr(msg_in, "task_id", None),
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg


@api_router.get("/messages/{other_user_id}", tags=["messages"])
def get_messages_with_user(
    other_user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    """Retourne l'historique des messages entre l'utilisateur connecté et other_user_id."""
    from sqlalchemy import or_, asc

    messages = (
        db.query(Message)
        .filter(
            or_(
                (Message.sender_id == current_user.id) & (Message.receiver_id == other_user_id),
                (Message.sender_id == other_user_id) & (Message.receiver_id == current_user.id),
            )
        )
        .order_by(asc(Message.id))
        .all()
    )

    return [
        {
            "id": msg.id,
            "content": msg.content,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "task_id": msg.task_id,
            "is_mine": msg.sender_id == current_user.id,
        }
        for msg in messages
    ]


@api_router.post("/reviews/", response_model=ReviewResponse, tags=["reviews"])
def create_review_root(
    *,
    db: Session = Depends(deps.get_db),
    review_in: ReviewCreate,
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    return create_review(db=db, review_in=review_in, current_user=current_user)


@api_router.get("/statistics/", tags=["statistics"])
def get_public_statistics(db: Session = Depends(deps.get_db)) -> Any:
    total_users = db.query(func.count(UserModel.id)).scalar() or 0
    total_tasks = db.query(func.count(TaskModel.id)).scalar() or 0
    total_applications = db.query(func.count(ApplicationModel.id)).scalar() or 0
    total_messages = db.query(func.count(Message.id)).scalar() or 0
    total_freelancers = (db.query(func.count(UserModel.id)).filter(UserModel.is_freelancer == True).scalar() or 0)
    total_clients = (db.query(func.count(UserModel.id)).filter(UserModel.is_client == True).scalar() or 0)

    freelancer_percentage = (total_freelancers / total_users * 100) if total_users > 0 else 0
    client_percentage = (total_clients / total_users * 100) if total_users > 0 else 0

    site_activity = float((total_users / total_users * 100) if total_users > 0 else 0)

    return {
        "numerical": {
            "total_users": total_users,
            "total_tasks": total_tasks,
            "total_applications": total_applications,
            "total_messages": total_messages,
        },
        "percentages": {
            "site_activity": round(site_activity, 2),
            "registration": {
                "freelancers": round(freelancer_percentage, 2),
                "clients": round(client_percentage, 2),
            },
        },
    }