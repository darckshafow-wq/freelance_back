from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.crud.crud_feedback import feedback as crud_feedback
from app.schemas.feedback import Feedback, FeedbackCreate, FeedbackReply
from app.models.user import User

user_router = APIRouter()
admin_router = APIRouter()
router = APIRouter()

router.include_router(user_router, tags=["feedback"])
router.include_router(admin_router, prefix="/admin", tags=["feedback-admin"])

@user_router.post("/", response_model=Feedback)
def create_feedback(
    *,
    db: Session = Depends(get_db),
    feedback_in: FeedbackCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Créer un nouveau feedback (Client ou Freelance)."""
    # Create manually because crud.create might expect an obj_in that matches exactly
    from app.models.feedback import Feedback as FeedbackModel
    db_obj = FeedbackModel(
        content=feedback_in.content,
        category=feedback_in.category,
        user_id=current_user.id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@user_router.get("/", response_model=List[Feedback])
def get_my_feedbacks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Récupère les feedbacks de l'utilisateur connecté."""
    # This route is used by both client and freelance
    feedbacks = crud_feedback.get_multi_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return feedbacks

@admin_router.get("/", response_model=List[Feedback])
def get_all_feedbacks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
) -> Any:
    """(Admin) Récupère tous les feedbacks.
    Cette route sera montée sur /admin/feedbacks.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    if status:
        feedbacks = crud_feedback.get_multi_by_status(db=db, status=status, skip=skip, limit=limit)
    else:
        feedbacks = crud_feedback.get_multi(db=db, skip=skip, limit=limit)
    return feedbacks

@admin_router.get("/{id}", response_model=Feedback)
def get_feedback(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """(Admin) Récupère un feedback par son ID."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    feedback_obj = crud_feedback.get(db=db, id=id)
    if not feedback_obj:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback_obj

@admin_router.put("/{id}/reply", response_model=Feedback)
def reply_feedback(
    id: int,
    *,
    db: Session = Depends(get_db),
    reply_in: FeedbackReply,
    current_user: User = Depends(get_current_user),
) -> Any:
    """(Admin) Répond à un feedback."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    feedback_obj = crud_feedback.get(db=db, id=id)
    if not feedback_obj:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback_obj = crud_feedback.reply_to_feedback(
        db=db, 
        db_obj=feedback_obj, 
        admin_reply=reply_in.admin_reply, 
        status=reply_in.status, 
        admin_id=current_user.id
    )
    return feedback_obj
