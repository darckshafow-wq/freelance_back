from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api.v1.deps import get_db, get_current_client
from app.schemas.project import ProjectCreate, ProjectOut, ProposalOut
from app.services.project_service import create_project, cancel_project, validate_submission
from app.services.proposal_service import accept_proposal
from app.models.user import User
from app.models.project import Project

router = APIRouter()

@router.post("/projects", response_model=ProjectOut)
def create_new_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    return create_project(db, current_user.id, project_in)

@router.get("/projects", response_model=List[ProjectOut])
def get_my_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    return db.query(Project).filter(Project.client_id == current_user.id).all()

@router.post("/projects/{project_id}/cancel", response_model=ProjectOut)
def cancel_my_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    return cancel_project(db, project_id, current_user.id)

@router.post("/proposals/{proposal_id}/accept", response_model=ProposalOut)
def accept_freelance_proposal(proposal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    return accept_proposal(db, proposal_id, current_user.id)

@router.post("/projects/{project_id}/validate", response_model=ProjectOut)
def validate_project_submission(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_client)):
    return validate_submission(db, project_id, current_user.id)
