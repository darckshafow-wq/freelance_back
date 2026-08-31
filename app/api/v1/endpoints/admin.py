from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_admin
from app.services.admin_service import toggle_user_suspension, delete_project_admin, get_platform_stats
from app.schemas.user import UserOut

router = APIRouter()

@router.post("/users/{user_id}/suspend", response_model=UserOut)
def suspend_user(user_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return toggle_user_suspension(db, user_id, True)

@router.post("/users/{user_id}/activate", response_model=UserOut)
def activate_user(user_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return toggle_user_suspension(db, user_id, False)

@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return delete_project_admin(db, project_id)

@router.get("/stats")
def platform_stats(db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    return get_platform_stats(db)
