from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.project import Project, ProjectStatus
from app.models.review import Review
from app.models.user import Profile
from app.schemas.review import ReviewCreate

def create_review(db: Session, reviewer_id: int, review_in: ReviewCreate) -> Review:
    project = db.query(Project).filter(Project.id == review_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.status != ProjectStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Reviews can only be left on COMPLETED projects")
        
    if reviewer_id == review_in.reviewee_id:
        raise HTTPException(status_code=400, detail="You cannot review yourself")

    # Check if a review already exists from this reviewer for this project
    existing_review = db.query(Review).filter(
        Review.project_id == project.id, 
        Review.reviewer_id == reviewer_id
    ).first()
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this project")

    # Create the review
    review = Review(
        project_id=review_in.project_id,
        reviewer_id=reviewer_id,
        reviewee_id=review_in.reviewee_id,
        rating=review_in.rating,
        comment=review_in.comment
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # Update profile average
    update_rating_average(db, review_in.reviewee_id)

    return review

def update_rating_average(db: Session, user_id: int):
    # Calculate new average
    reviews = db.query(Review).filter(Review.reviewee_id == user_id).all()
    if not reviews:
        return
        
    total_rating = sum(r.rating for r in reviews)
    new_average = total_rating / len(reviews)
    
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if profile:
        profile.rating_average = new_average
        db.commit()
