from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, decode_access_token, decode_refresh_token
from app.models.user import User


class AuthService:
    def issue_tokens(self, db: Session, user: User) -> dict[str, object]:
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        user.refresh_token = refresh_token
        user.refresh_token_expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user.id,
            "is_verified": user.is_verified,
        }

    def refresh(self, db: Session, refresh_token: str) -> Optional[dict[str, object]]:
        user_id = decode_refresh_token(refresh_token)
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.refresh_token or user.refresh_token != refresh_token:
            return None

        if user.refresh_token_expires_at:
            expires_at = datetime.fromisoformat(user.refresh_token_expires_at)
            if datetime.now(timezone.utc) > expires_at:
                return None

        return self.issue_tokens(db, user)


auth_service = AuthService()
