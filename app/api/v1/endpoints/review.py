from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_user
from app.schemas.review import ReviewCreate, ReviewOut
from app.services.review_service import create_review
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=ReviewOut)
def leave_review(review_in: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_review(db, current_user.id, review_in)
