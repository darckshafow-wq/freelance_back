from sqlalchemy.orm import Session

from app.crud.crud_notification import notification as crud_notification
from app.models.notifications import Notification
from app.schemas.notification_schema import NotificationCreate


class NotificationService:
    def create_for_user(self, db: Session, user_id: int, message: str, is_read: bool = False) -> Notification:
        payload = NotificationCreate(message=message, user_id=user_id, is_read=is_read)
        return crud_notification.create(db, obj_in=payload)

    def mark_as_read(self, db: Session, notification: Notification) -> Notification:
        return crud_notification.mark_as_read(db, db_obj=notification)


notification_service = NotificationService()
