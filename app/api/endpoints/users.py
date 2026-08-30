from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.crud_user import user as crud_user
from app.schemas.user import User, UserCreate
from app.api import deps
from app.models.user import User as UserModel
from app.models.review import Review
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ReviewCreate(BaseModel):
    comment: str
    rating: float
    task_id: int
    reviewee_id: int

class ReviewResponse(BaseModel):
    id: int
    comment: str
    rating: float
    task_id: int
    reviewer_id: int
    reviewee_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

router = APIRouter()

@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
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
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    return read_user_profile(user_id=current_user.id, db=db)

@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/profile")
def read_user_profile(
    user_id: int,
    db: Session = Depends(deps.get_db),
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
        profile_data["posted_tasks"] = [{"id": t.id, "title": t.title, "status": t.status.value} for t in user.created_tasks]
        
    # Si le user est freelance, on renvoie ses candidatures
    if user.is_freelancer:
        profile_data["applications"] = [{"id": a.id, "task_id": a.task_id, "status": a.status.value} for a in user.applications]
        
    return profile_data


# ─── REVIEWS (Route globale, accessible par tous les rôles) ──────────────────────

@router.get("/reviews/", response_model=List[ReviewResponse], summary="Avis reçus par un profil")
def get_reviews(
    db: Session = Depends(deps.get_db),
    reviewee_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    Récupère les avis d'un profil via ?reviewee_id=<id>.
    Sans paramètre, retourne tous les avis (usage admin).
    """
    query = db.query(Review)
    if reviewee_id is not None:
        query = query.filter(Review.reviewee_id == reviewee_id)
    reviews = query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    return reviews


@router.post("/reviews/", response_model=ReviewResponse, summary="Laisser un avis sur un profil")
def create_review(
    *,
    db: Session = Depends(deps.get_db),
    review_in: ReviewCreate,
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    """
    Crée un avis sur un profil à la suite d'une mission accomplie.
    """
    review = Review(
        comment=review_in.comment,
        rating=review_in.rating,
        task_id=review_in.task_id,
        reviewer_id=current_user.id,
        reviewee_id=review_in.reviewee_id,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
