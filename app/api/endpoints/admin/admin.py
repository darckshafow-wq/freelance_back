from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.crud_task import task as crud_task
from app.crud.crud_user import user as crud_user
from app.schemas.task import Task, TaskUpdate
from app.schemas.user import User
from app.models.user import User as UserModel
from sqlalchemy import func
from app.models.task import TaskStatus, Task as TaskModel
from app.models.application import Application, ApplicationStatus
from app.models.message import Message
from app.models.notifications import Notification as NotificationModel
from app.crud.crud_notification import notification as crud_notification
from app.schemas.notification_schema import Notification as NotificationSchema, NotificationCreate
from app.services.notification_service import notification_service
from app.models.review import Review
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone

class ReviewResponse(BaseModel):
    id: int
    comment: str
    rating: float
    task_id: int
    reviewer_id: int
    reviewee_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

router = APIRouter(dependencies=[Depends(deps.log_action)])

_BROADCAST_HISTORY: list[dict[str, Any]] = []


@router.get("/audit", summary="Audit: usage par rôle (admin)")
def get_audit_stats(
    db: Session = Depends(deps.get_db),
    _: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    from app.crud.crud_audit import audit as crud_audit

    recent = crud_audit.get_recent(db, limit=200)
    agg = crud_audit.aggregate_by_role(db)
    return {"aggregated_by_role": agg, "recent": [
        {"user_id": r.user_id, "path": r.path, "method": r.method, "role": r.role, "created_at": r.created_at.isoformat()} for r in recent
    ]}


@router.get("/tasks", response_model=List[Task], summary="Toutes les missions (admin)")
def read_all_tasks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    _: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    tasks = crud_task.get_multi(db, skip=skip, limit=limit)
    return tasks


@router.put("/tasks/{task_id}", response_model=Task, summary="Modifier le statut d'une mission (admin)")
def update_task_status(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    task_in: TaskUpdate,
    _: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    task = crud_task.get(db, id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Mission introuvable")
    task = crud_task.update(db=db, db_obj=task, obj_in=task_in)
    return task


@router.get("/users", response_model=List[User], summary="Tous les utilisateurs (admin)")
def read_all_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    _: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    users = crud_user.get_multi(db, skip=skip, limit=limit)
    return users


@router.delete("/users/{user_id}", summary="Supprimer un utilisateur (admin)")
def delete_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_admin: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")
    db.delete(user)
    db.commit()
    return {"deleted": True, "user_id": user_id}

@router.put("/users/{user_id}/verify", summary="Valider un utilisateur (admin)")
def verify_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    _: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if not user.is_verified:
        user.is_verified = True
        db.add(user)
        db.commit()
        db.refresh(user)

    return {"verified": True, "user_id": user_id, "is_verified": user.is_verified}

# ─── SECTION STATISTIQUES ─────────────────────────────────────────────

@router.get("/dashboard/stats", summary="Statistiques générales du dashboard")
def get_dashboard_stats(
    db: Session = Depends(deps.get_db), 
    _: UserModel = Depends(deps.get_current_active_admin)
) -> Any:
    total_users = db.query(func.count(UserModel.id)).scalar() or 0
    total_freelancers = db.query(func.count(UserModel.id)).filter(UserModel.is_freelancer == True).scalar() or 0
    total_clients = db.query(func.count(UserModel.id)).filter(UserModel.is_client == True).scalar() or 0
    total_admins = db.query(func.count(UserModel.id)).filter(UserModel.is_admin == True).scalar() or 0

    total_tasks = db.query(func.count(TaskModel.id)).scalar() or 0
    pending_tasks = db.query(func.count(TaskModel.id)).filter(TaskModel.status == TaskStatus.PENDING).scalar() or 0
    validated_tasks = db.query(func.count(TaskModel.id)).filter(TaskModel.status == TaskStatus.VALIDATED).scalar() or 0
    tasks_with_applications = db.query(func.count(func.distinct(Application.task_id))).scalar() or 0

    total_messages = db.query(func.count(Message.id)).scalar() or 0
    total_applications = db.query(func.count(Application.id)).scalar() or 0
    pending_applications = db.query(func.count(Application.id)).filter(Application.status == ApplicationStatus.PENDING).scalar() or 0

    freelancer_percentage = (total_freelancers / total_users * 100) if total_users > 0 else 0
    client_percentage = (total_clients / total_users * 100) if total_users > 0 else 0
    validated_task_percentage = (validated_tasks / total_tasks * 100) if total_tasks > 0 else 0
    tasks_applied_percentage = (tasks_with_applications / total_tasks * 100) if total_tasks > 0 else 0

    active_users_query = db.query(UserModel.id).join(Message, UserModel.id == Message.sender_id, isouter=True) \
                           .join(TaskModel, UserModel.id == TaskModel.client_id, isouter=True) \
                           .join(Application, UserModel.id == Application.freelance_id, isouter=True) \
                           .filter((Message.id != None) | (TaskModel.id != None) | (Application.id != None))
    active_users = active_users_query.distinct().count()
    site_activity_percentage = (active_users / total_users * 100) if total_users > 0 else 0

    return {
        "users": {
            "total": total_users,
            "freelancers": total_freelancers,
            "clients": total_clients,
            "admins": total_admins
        },
        "tasks": {
            "total": total_tasks,
            "pending": pending_tasks,
            "validated": validated_tasks,
            "applied_to": tasks_with_applications
        },
        "applications": {
            "total": total_applications,
            "pending": pending_applications
        },
        "messages": {
            "total": total_messages
        },
        "percentages": {
            "site_activity": round(site_activity_percentage, 2),
            "registration": {
                "freelancers": round(freelancer_percentage, 2),
                "clients": round(client_percentage, 2)
            },
            "tasks": {
                "validated": round(validated_task_percentage, 2),
                "applied": round(tasks_applied_percentage, 2)
            }
        }
    }

# ─── SECTION AVIS ──────────────────────────────────────────────────────

@router.get("/reviews", response_model=List[ReviewResponse], summary="Tous les avis (admin)")
def get_all_reviews(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    _: UserModel = Depends(deps.get_current_active_admin)
) -> Any:
    reviews = db.query(Review).offset(skip).limit(limit).all()
    return reviews

# ─── SECTION NOTIFICATIONS ─────────────────────────────────────────────

@router.get("/notifications", response_model=List[NotificationSchema], summary="Mes notifications")
def get_admin_notifications(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    notifs = (
        db.query(NotificationModel)
        .filter(NotificationModel.user_id == current_user.id)
        .order_by(NotificationModel.created_at.desc())
        .all()
    )
    return notifs

@router.post("/notifications", response_model=NotificationSchema, summary="Créer une notification")
def create_admin_notification(
    *,
    db: Session = Depends(deps.get_db),
    message_in: NotificationCreate,
    current_user: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    if message_in.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    notif = notification_service.create_for_user(db, user_id=message_in.user_id, message=message_in.message, is_read=message_in.is_read)
    return notif

@router.get("/notifications/broadcast", summary="Historique des broadcasts")
def list_admin_broadcasts(
    current_user: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    return [dict(entry) for entry in _BROADCAST_HISTORY]


@router.post("/notifications/broadcast", summary="Diffuser une notification à un rôle")
def broadcast_admin_notification(
    *,
    db: Session = Depends(deps.get_db),
    title: str,
    content: str,
    target_role: str = "all",
    current_user: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    if not title or not content:
        raise HTTPException(status_code=400, detail="title and content are required")

    query = db.query(UserModel)
    if target_role == "freelance":
        query = query.filter(UserModel.is_freelancer == True)
    elif target_role == "client":
        query = query.filter(UserModel.is_client == True)
    elif target_role != "all":
        raise HTTPException(status_code=400, detail="target_role must be one of: all, freelance, client")

    recipients = query.filter(UserModel.is_active == True).all()
    message = f"{title}: {content}"
    created = 0

    for user in recipients:
        if user.id == current_user.id:
            continue
        notif = NotificationCreate(message=message, user_id=user.id, is_read=False)
        crud_notification.create(db, obj_in=notif)
        created += 1

    _BROADCAST_HISTORY.append(
        {
            "id": len(_BROADCAST_HISTORY) + 1,
            "title": title,
            "body": content,
            "type": "system",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "related_id": None,
            "action_route": None,
        }
    )

    return {"created": created, "target_role": target_role, "message": message}

@router.post("/notifications/{notification_id}/read", response_model=NotificationSchema, summary="Marquer comme lue")
def read_admin_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    db_notification = crud_notification.get(db, id=notification_id)
    if not db_notification or db_notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    return notification_service.mark_as_read(db, notification=db_notification)

@router.delete("/notifications/{notification_id}", summary="Supprimer une notification")
def delete_admin_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_admin),
) -> Any:
    db_notification = crud_notification.get(db, id=notification_id)
    if not db_notification or db_notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    db.delete(db_notification)
    db.commit()
    return {"deleted": True, "id": notification_id}
