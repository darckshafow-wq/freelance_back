from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.message import Message
from app.models.task import Task
from app.schemas.user import User

from pydantic import BaseModel
from datetime import datetime

class MessageCreate(BaseModel):
    content: str
    receiver_id: int
    task_id: int | None = None

class MessageResponse(BaseModel):
    id: int
    content: str
    sender_id: int
    receiver_id: int
    task_id: int | None
    timestamp: datetime

    class Config:
        from_attributes = True

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For the sake of simplicity without a central auth system in this boilerplate, 
# we mock the current user by receiving it as a header or just defaulting to user 1.
# Usually this would be Depends(get_current_user)
def get_current_user_mock(db: Session = Depends(get_db)):
    from app.crud.crud_user import user as crud_user
    u = crud_user.get(db, id=1)
    if not u:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return u

@router.post("/", response_model=MessageResponse)
async def create_message(
    *,
    db: Session = Depends(get_db),
    msg_in: MessageCreate,
    current_user: User = Depends(get_current_user_mock)
) -> Any:
    """
    Create new message.
    """
    # Verify task if task_id provided
    if msg_in.task_id:
        task = db.query(Task).filter(Task.id == msg_in.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
    db_msg = Message(
        content=msg_in.content,
        sender_id=current_user.id,
        receiver_id=msg_in.receiver_id,
        task_id=msg_in.task_id
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    
    # Notify receiver via WebSocket
    from app.websockets.manager import manager
    import json
    notification_data = {
        "type": "new_message",
        "message_id": db_msg.id,
        "sender_id": current_user.id,
        "content": db_msg.content
    }
    await manager.send_json_message(notification_data, msg_in.receiver_id)
    
    return db_msg

@router.get("/{other_user_id}", response_model=List[MessageResponse])
def get_conversation(
    other_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_mock),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get conversation with another user.
    """
    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.desc()).offset(skip).limit(limit).all()
    
    return messages
