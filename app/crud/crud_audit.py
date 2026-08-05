from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.audit import AuditLog


class CRUDAudit:
    def create(self, db: Session, user_id: Optional[int], path: str, method: str, role: Optional[str]) -> AuditLog:
        db_obj = AuditLog(user_id=user_id, path=path, method=method, role=role)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_recent(self, db: Session, limit: int = 100) -> List[AuditLog]:
        return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()

    def aggregate_by_role(self, db: Session):
        rows = db.query(AuditLog.role, func.count(AuditLog.id)).group_by(AuditLog.role).all()
        return {r[0] or "unknown": r[1] for r in rows}


audit = CRUDAudit()
