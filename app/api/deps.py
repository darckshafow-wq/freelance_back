from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi import Request

from app.db.session import SessionLocal
from app.crud.crud_user import user as crud_user
from app.models.user import User
from app.core.security import decode_access_token

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login/access-token"
)


def get_token_from_request(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")
    return authorization.replace("Bearer ", "", 1)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> User:
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte désactivé",
        )
    return user


def log_action(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> None:
    """Dependency that records the current request and user id/role into the audit log.

    This intentionally does NOT depend on `get_current_user` to avoid returning an ORM instance
    that could be detached later during dependency resolution.
    """
    try:
        from app.crud.crud_audit import audit as crud_audit
        from app.models.user import User as UserModel
        from app.core.security import decode_access_token

        user_id = decode_access_token(token)
        role = "unknown"
        if user_id:
            row = db.query(UserModel.id, UserModel.is_admin, UserModel.is_client, UserModel.is_freelancer).filter(UserModel.id == user_id).first()
            if row:
                is_admin = bool(row[1])
                is_client = bool(row[2])
                is_freelancer = bool(row[3])
                role = "admin" if is_admin else ("client" if is_client else ("freelancer" if is_freelancer else "unknown"))
        crud_audit.create(db=db, user_id=user_id, path=str(request.url.path), method=request.method, role=role)
    except Exception:
        # Do not raise on audit failures
        pass


def get_current_active_client(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_client and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Réservé aux clients")
    return current_user


def get_current_active_freelancer(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_freelancer and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Réservé aux freelancers")
    return current_user


def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    return current_user


def get_current_user_id(
    current_user: User = Depends(get_current_user),
) -> int:
    return current_user.id
