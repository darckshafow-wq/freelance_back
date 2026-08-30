from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.notifications import Notification
from app.models.task import Task
from app.models.user import User


class ApplicationService:
    def accept_application(self, db: Session, application: Application, current_user: User) -> Application:
        task = db.query(Task).filter(Task.id == application.task_id).first()

        if task and task.client_id != current_user.id and not current_user.is_admin:
            raise PermissionError("Vous n'êtes pas le propriétaire de cette mission")

        application.status = ApplicationStatus.ACCEPTED
        if task is not None:
            task.freelancer_id = application.freelance_id
        db.add(application)
        db.add(task) if task is not None else None

        if application.freelance_id:
            notification = Notification(
                message=f"Votre candidature pour '{task.title if task else 'cette mission'}' a été acceptée.",
                user_id=application.freelance_id,
                is_read=False,
            )
            db.add(notification)

        db.commit()
        db.refresh(application)
        return application

    def reject_application(self, db: Session, application: Application, current_user: User) -> Application:
        task = db.query(Task).filter(Task.id == application.task_id).first()

        if task and task.client_id != current_user.id and not current_user.is_admin:
            raise PermissionError("Vous n'êtes pas le propriétaire de cette mission")

        application.status = ApplicationStatus.REJECTED
        db.add(application)

        if application.freelance_id:
            notification = Notification(
                message=f"Votre candidature pour '{task.title if task else 'cette mission'}' a été refusée.",
                user_id=application.freelance_id,
                is_read=False,
            )
            db.add(notification)

        db.commit()
        db.refresh(application)
        return application


application_service = ApplicationService()
