from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.crud_task import task as crud_task
from app.schemas.task import Task, TaskCreate
from app.db.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Temporary mock for current user
def get_current_user_id() -> int:
    return 1 # In production, extract from JWT token

@router.post("/", response_model=Task)
def create_task(
    *,
    db: Session = Depends(get_db),
    task_in: TaskCreate,
    client_id: int = Depends(get_current_user_id),
) -> Any:
    """
    Create new task (Client only)
    """
    # Note: here we'd verify if client_id belongs to a user with `is_client == True`
    task = crud_task.create_with_client(db=db, obj_in=task_in, client_id=client_id)
    return task

@router.get("/", response_model=List[Task])
def read_tasks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all validated tasks for freelancers to view.
    """
    from app.models.task import TaskStatus
    tasks = crud_task.get_multi_by_status(db, status=TaskStatus.VALIDATED, skip=skip, limit=limit)
    return tasks

@router.get("/my-tasks", response_model=List[Task])
def read_my_tasks(
    db: Session = Depends(get_db),
    client_id: int = Depends(get_current_user_id),
) -> Any:
    """
    Retrieve tasks created by the current client.
    """
    tasks = crud_task.get_multi_by_client(db, client_id=client_id)
    return tasks
