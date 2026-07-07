from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.review import Review, ReviewType
from app.schemas.user import User
from pydantic import BaseModel
from datetime import datetime

class ReviewCreate(BaseModel):
    content: str
    review_type: ReviewType = ReviewType.SUGGESTION

class ReviewResponse(BaseModel):
    id: int
    content: str
    review_type: ReviewType
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_mock(db: Session = Depends(get_db)):
    from app.crud.crud_user import user as crud_user
    u = crud_user.get(db, id=1)
    if not u:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return u

@router.post("/", response_model=ReviewResponse)
def create_review(
    *,
    db: Session = Depends(get_db),
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user_mock)
) -> Any:
    """
    Create a new platform review/feedback.
    """
    review = Review(
        content=review_in.content,
        review_type=review_in.review_type,
        user_id=current_user.id
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

@router.get("/", response_model=List[ReviewResponse])
def get_reviews(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all reviews. (Could be restricted to admins)
    """
    reviews = db.query(Review).offset(skip).limit(limit).all()
    return reviews
