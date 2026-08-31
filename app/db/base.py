from app.db.base_class import Base

# Import all models here so Alembic can see them
from app.models.user import User, Profile
from app.models.category import Category
from app.models.project import Project, Proposal
from app.models.message import Message
from app.models.notification import Notification
from app.models.review import Review
from app.models.feedback import Feedback
from app.models.report import Report
from app.models.audit import AuditLog
from app.models.system_warning import SystemWarning
