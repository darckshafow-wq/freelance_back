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

    def get_chat_contacts_for_freelance(self, db: Session, freelance_id: int) -> List[dict]:
        """
        Retourne la liste simplifiée de tous les clients uniques avec qui 
        le freelance possède une candidature acceptée.
        """
        from app.models.task import Task
        from app.models.user import User

        accepted_apps = (
            db.query(Application)
            .filter(
                Application.freelance_id == freelance_id,
                Application.status == ApplicationStatus.ACCEPTED
            )
            .all()
        )

        contacts = []
        seen_client_ids = set()

        for app in accepted_apps:
            task = db.query(Task).filter(Task.id == app.task_id).first()
            if not task:
                continue

            client = db.query(User).filter(User.id == task.client_id).first()
            if not client or client.id in seen_client_ids:
                continue

            seen_client_ids.add(client.id)

            contacts.append({
                "client_id": client.id,
                "client_name": client.full_name,
                "task_id": task.id,
                "task_title": task.title
            })

        return contacts

    def get_chat_with_messages_for_freelance(self, db: Session, freelance_id: int) -> List[dict]:
        """
        Retourne la liste des discussions acceptées avec le nom du client,
        le titre de la tâche, et l'historique COMPLET des messages en commun.
        """
        from app.models.task import Task
        from app.models.user import User
        from app.models.message import Message

        accepted_apps = (
            db.query(Application)
            .filter(
                Application.freelance_id == freelance_id,
                Application.status == ApplicationStatus.ACCEPTED
            )
            .all()
        )

        chat_list = []

        for app in accepted_apps:
            task = db.query(Task).filter(Task.id == app.task_id).first()
            if not task:
                continue

            client = db.query(User).filter(User.id == task.client_id).first()
            if not client:
                continue

            messages_records = (
                db.query(Message)
                .filter(Message.task_id == task.id)
                # Dans /backend/app/crud/crud_application.py
# Remplace Message.created_at.asc() par :
                .order_by(Message.timestamp.asc())
                .all()
            )

            messages_list = [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "receiver_id": msg.receiver_id,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in messages_records
            ]

            chat_list.append({
                "client_name": client.full_name,
                "task_title": task.title,
                "task_id": task.id,
                "application_id": app.id,
                "messages": messages_list
            })

        return chat_list

    def update_status(self, db: Session, db_obj: Application, status: ApplicationStatus) -> Application:
        db_obj.status = status
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