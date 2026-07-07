from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.crud_task import task as crud_task
from app.schemas.task import Task, TaskUpdate
from app.db.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Temporary mock for admin check
def check_is_admin() -> bool:
    return True

@router.get("/tasks", response_model=List[Task])
def read_all_tasks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    is_admin: bool = Depends(check_is_admin)
) -> Any:
    """
    Retrieve all tasks, regardless of status (Admin only).
    """
    tasks = crud_task.get_multi(db, skip=skip, limit=limit)
    return tasks

@router.put("/tasks/{task_id}", response_model=Task)
def update_task_status(
    *,
    db: Session = Depends(get_db),
    task_id: int,
    task_in: TaskUpdate,
    is_admin: bool = Depends(check_is_admin)
) -> Any:
    """
    Update a task status (Admin only).
    """
    task = crud_task.get(db, id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task = crud_task.update(db=db, db_obj=task, obj_in=task_in)
    return task
