from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud.crud_application import application as crud_app
from app.crud.crud_task import task as crud_task
from app.schemas.application import Application, ApplicationCreate
from app.db.session import SessionLocal
from app.models.task import TaskStatus, Task
from app.models.application import Application as ApplicationModel, ApplicationStatus

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_freelance_id() -> int:
    return 2 # Mock

@router.post("/", response_model=Application)
def apply_for_task(
    *,
    db: Session = Depends(get_db),
    app_in: ApplicationCreate,
    freelance_id: int = Depends(get_current_freelance_id),
) -> Any:
    """
    Apply for a specific task.
    """
    task = crud_task.get(db, id=app_in.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.VALIDATED:
        raise HTTPException(status_code=400, detail="Can only apply to validated tasks")
        
    application = crud_app.create_with_freelance(db=db, obj_in=app_in, freelance_id=freelance_id)
    return application

@router.get("/task/{task_id}", response_model=List[Application])
def read_applications_for_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all applications for a task (Client view).
    """
    apps = crud_app.get_multi_by_task(db, task_id=task_id)
    return apps

@router.get("/my-applications")
def get_my_applications(
    db: Session = Depends(get_db),
    freelance_id: int = Depends(get_current_freelance_id),
    status: Optional[str] = Query(None, description="Filter by status: pending, accepted, rejected"),
) -> Any:
    """
    Get all applications for the current freelancer, enriched with task info.
    """
    query = db.query(ApplicationModel).filter(
        ApplicationModel.freelance_id == freelance_id
    )
    
    if status:
        try:
            status_enum = ApplicationStatus(status.lower())
            query = query.filter(ApplicationModel.status == status_enum)
        except ValueError:
            pass
    
    apps = query.all()
    
    result = []
    for app in apps:
        task = db.query(Task).filter(Task.id == app.task_id).first()
        result.append({
            "id": app.id,
            "task_id": app.task_id,
            "task_title": task.title if task else "Mission supprimée",
            "client_id": task.client_id if task else 0,
            "cover_letter": app.message or "",
            "proposed_budget": task.price if task else 0,
            "status": app.status.value if app.status else "pending",
            "created_at": None,  # Add if you have a created_at column
        })
    
    return result

