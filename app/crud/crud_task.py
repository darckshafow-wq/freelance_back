from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate

class CRUDTask:
    def get(self, db: Session, id: int) -> Optional[Task]:
        return db.query(Task).filter(Task.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Task]:
        return db.query(Task).offset(skip).limit(limit).all()
        
    def get_multi_by_status(self, db: Session, status: TaskStatus, skip: int = 0, limit: int = 100) -> List[Task]:
        return db.query(Task).filter(Task.status == status).offset(skip).limit(limit).all()

    def get_multi_by_client(self, db: Session, client_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
        return db.query(Task).filter(Task.client_id == client_id).offset(skip).limit(limit).all()

    def create_with_client(self, db: Session, obj_in: TaskCreate, client_id: int) -> Task:
        db_obj = Task(
            title=obj_in.title,
            description=obj_in.description,
            price=obj_in.price,
            location=obj_in.location,
            client_id=client_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Task, obj_in: TaskUpdate) -> Task:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

task = CRUDTask()
