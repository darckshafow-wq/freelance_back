# app/db/base.py
from app.db.base_class import Base  # noqa
# Import all models here so Alembic can see them
from app.models.user import User
from app.models.task import Task
from app.models.application import Application
from app.models.message import Message
from app.models.notifications import Notification
from app.models.review import Review
