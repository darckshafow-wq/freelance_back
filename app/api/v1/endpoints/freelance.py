from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api.v1.deps import get_db, get_current_freelance
from app.schemas.project import ProposalCreate, ProposalOut, ProjectOut
from app.services.proposal_service import create_proposal, submit_work
from app.models.user import User
from app.models.project import Project, ProjectStatus

router = APIRouter()

@router.get("/projects", response_model=List[ProjectOut])
def list_available_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    return db.query(Project).filter(Project.status == ProjectStatus.OPEN).all()

@router.post("/projects/{project_id}/proposals", response_model=ProposalOut)
def apply_to_project(project_id: int, proposal_in: ProposalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    return create_proposal(db, project_id, current_user.id, proposal_in)

@router.post("/projects/{project_id}/submit", response_model=ProjectOut)
def submit_project_work(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_freelance)):
    return submit_work(db, project_id, current_user.id)
