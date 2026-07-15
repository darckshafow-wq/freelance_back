from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.crud_notification import notification as crud_notification
from app.schemas.notification_schema import Notification, NotificationCreate
from app.api import deps
from app.models.notifications import Notification as NotificationModel

router = APIRouter()


@router.get("/", response_model=List[Notification])
def get_notifications(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    """Retourne toutes les notifications de l'utilisateur connecté."""
    notifs = (
        db.query(NotificationModel)
        .filter(NotificationModel.user_id == current_user.id)
        .order_by(NotificationModel.created_at.desc())
        .all()
    )
    return notifs


@router.post("/", response_model=Notification)
def create_notification(
    *,
    db: Session = Depends(deps.get_db),
    message_in: NotificationCreate,
    current_user=Depends(deps.get_current_user),
) -> Any:
    notif = crud_notification.create(db, obj_in=message_in)
    if notif is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@router.post("/{notification_id}/read", response_model=Notification)
def read_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    db_notification = crud_notification.get(db, id=notification_id)
    if not db_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification non trouvée"
        )
    updated_notification = crud_notification.mark_as_read(db, db_obj=db_notification)
    return updated_notification


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    db_notification = crud_notification.get(db, id=notification_id)
    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    if db_notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    db.delete(db_notification)
    db.commit()
    return {"deleted": True, "id": notification_id}