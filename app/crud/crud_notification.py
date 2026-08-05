from typing import Optional
from sqlalchemy.orm import Session
from app.models.notifications import Notification
from app.schemas.notification_schema import NotificationCreate, NotificationUpdate


class CRUDNotification:
    def get(self, db: Session, id: int) -> Optional[Notification]:
        return db.query(Notification).filter(Notification.id == id).first()

    def create(self, db: Session, obj_in: NotificationCreate) -> Notification:
        db_obj = Notification(
            message=obj_in.message,
            is_read=obj_in.is_read,
            user_id=obj_in.user_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Notification, obj_in: NotificationUpdate) -> Notification:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def mark_as_read(self, db: Session, db_obj: Notification) -> Notification:
        db_obj.is_read = True
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


notification = CRUDNotification()