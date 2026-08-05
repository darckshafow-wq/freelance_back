from typing import List
from sqlalchemy.orm import Session
from app.db.base_class import Base
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate
from datetime import datetime


class CRUDBase:
    def __init__(self, model):
        self.model = model

    def get(self, db: Session, id: int):
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100):
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in):
        db_obj = self.model(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int):
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

class CRUDFeedback(CRUDBase):
    def get_multi_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Feedback]:
        return db.query(self.model).filter(Feedback.user_id == user_id).offset(skip).limit(limit).all()

    def get_multi_by_status(self, db: Session, *, status: str, skip: int = 0, limit: int = 100) -> List[Feedback]:
        return db.query(self.model).filter(Feedback.status == status).offset(skip).limit(limit).all()

    def reply_to_feedback(self, db: Session, *, db_obj: Feedback, admin_reply: str, status: str, admin_id: int) -> Feedback:
        db_obj.admin_reply = admin_reply
        db_obj.status = status
        db_obj.replied_at = datetime.utcnow()
        db_obj.replied_by = admin_id
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

feedback = CRUDFeedback(Feedback)
