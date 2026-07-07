from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationStatus
from app.schemas.application import ApplicationCreate, ApplicationUpdate

class CRUDApplication:
    def get(self, db: Session, id: int) -> Optional[Application]:
        return db.query(Application).filter(Application.id == id).first()

    def get_multi_by_task(self, db: Session, task_id: int, skip: int = 0, limit: int = 100) -> List[Application]:
        return db.query(Application).filter(Application.task_id == task_id).offset(skip).limit(limit).all()

    def get_multi_by_freelance(self, db: Session, freelance_id: int, skip: int = 0, limit: int = 100) -> List[Application]:
        return db.query(Application).filter(Application.freelance_id == freelance_id).offset(skip).limit(limit).all()

    def create_with_freelance(self, db: Session, obj_in: ApplicationCreate, freelance_id: int) -> Application:
        db_obj = Application(
            message=obj_in.message,
            task_id=obj_in.task_id,
            freelance_id=freelance_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Application, obj_in: ApplicationUpdate) -> Application:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

application = CRUDApplication()
