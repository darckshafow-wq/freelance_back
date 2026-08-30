"""
Client-specific endpoints:
- POST   /client/tasks           : Créer une mission
- GET    /client/tasks           : Mes missions créées
- GET    /client/tasks/{id}/applications : Candidatures reçues pour une mission
- PUT    /client/applications/{id}/accept : Accepter une candidature
- PUT    /client/applications/{id}/reject : Rejeter une candidature
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.crud_task import task as crud_task
from app.crud.crud_application import application as crud_app
from app.schemas.task import Task, TaskCreate
from app.schemas.application import Application
from app.models.user import User
from app.models.application import ApplicationStatus
from app.models.notifications import Notification as NotificationModel
from app.crud.crud_notification import notification as crud_notification
from app.schemas.notification_schema import Notification as NotificationSchema, NotificationCreate
from app.services.application_service import application_service
from app.services.notification_service import notification_service
from app.api.endpoints.feedback import user_router as feedback_user_router
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone


router = APIRouter()

router.include_router(feedback_user_router, prefix="/feedback", tags=["client-feedback"])


@router.post("/tasks", response_model=Task, summary="Créer une mission")
def create_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: TaskCreate,
    current_user: User = Depends(deps.get_current_active_client),
) -> Any:
    task = crud_task.create_with_client(db=db, obj_in=task_in, client_id=current_user.id)
    return task


@router.get("/tasks", response_model=List[Task], summary="Mes missions créées")
def get_my_tasks(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_client),
) -> Any:
    tasks = crud_task.get_multi_by_client(db, client_id=current_user.id)
    return tasks


@router.get("/tasks/{task_id}/applications", response_model=List[Application], summary="Candidatures reçues pour une mission")
def get_applications_for_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_client),
) -> Any:
    task = crud_task.get(db, id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Mission introuvable")
    if task.client_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas le propriétaire de cette mission")

    apps = crud_app.get_multi_by_task(db, task_id=task_id)
    return apps


@router.put("/applications/{application_id}/accept", response_model=Application, summary="Accepter une candidature")
def accept_application(
    application_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_client),
) -> Any:
    app = crud_app.get(db, id=application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Candidature introuvable")

    try:
        updated = application_service.accept_application(db, application=app, current_user=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return updated


@router.put("/applications/{application_id}/reject", response_model=Application, summary="Rejeter une candidature")
def reject_application(
    application_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_client),
) -> Any:
    app = crud_app.get(db, id=application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Candidature introuvable")

    try:
        updated = application_service.reject_application(db, application=app, current_user=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return updated

# ─── SECTION NOTIFICATIONS ─────────────────────────────────────────────

@router.get("/notifications", response_model=List[NotificationSchema], summary="Mes notifications")
def get_client_notifications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_client),
) -> Any:
    notifs = (
        db.query(NotificationModel)
        .filter(NotificationModel.user_id == current_user.id)
        .order_by(NotificationModel.created_at.desc())
        .all()
    )
    return notifs

@router.post("/notifications", response_model=NotificationSchema, summary="Créer une notification")
def create_client_notification(
    *,
    db: Session = Depends(deps.get_db),
    message_in: NotificationCreate,
    current_user: User = Depends(deps.get_current_active_client),
) -> Any:
    # Ensure the notification is for the current user
    if message_in.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    notif = notification_service.create_for_user(db, user_id=message_in.user_id, message=message_in.message, is_read=message_in.is_read)
    return notif

@router.post("/notifications/{notification_id}/read", response_model=NotificationSchema, summary="Marquer comme lue")
def read_client_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_client),
) -> Any:
    db_notification = crud_notification.get(db, id=notification_id)
    if not db_notification or db_notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    return notification_service.mark_as_read(db, notification=db_notification)

@router.delete("/notifications/{notification_id}", summary="Supprimer une notification")
def delete_client_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_client),
) -> Any:
    db_notification = crud_notification.get(db, id=notification_id)
    if not db_notification or db_notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    db.delete(db_notification)
    db.commit()
    return {"deleted": True, "id": notification_id}


