from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.crud_user import user as crud_user
from app.schemas.user import User, UserCreate
from app.db.session import SessionLocal
from app.api import deps
from app.models.user import User as UserModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud_user.create(db, obj_in=user_in)
    return user

@router.get("/me", response_model=User)
def read_user_me(
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    return current_user

@router.get("/me/profile")
def read_user_me_profile(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    return read_user_profile(user_id=current_user.id, db=db)

@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
) -> Any:
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/profile")
def read_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a complete profile of a user (pseudo/full_name, stats depending on role).
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    profile_data = {
        "id": user.id,
        "pseudo": user.full_name, # Using full_name as pseudo
        "email": user.email,
        "location": user.location,
        "roles": {
            "is_admin": user.is_admin,
            "is_client": user.is_client,
            "is_freelancer": user.is_freelancer
        }
    }
    
    # Si le user est client, on renvoie ses tâches créées
    if user.is_client:
        profile_data["posted_tasks"] = [{"id": t.id, "title": t.title, "status": t.status.value} for t in user.tasks]
        
    # Si le user est freelance, on renvoie ses candidatures
    if user.is_freelancer:
        profile_data["applications"] = [{"id": a.id, "task_id": a.task_id, "status": a.status.value} for a in user.applications]
        
    return profile_data
