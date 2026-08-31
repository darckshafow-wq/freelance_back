from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db
from app.services.websocket_manager import manager, save_and_broadcast_message
from app.models.project import Project, ProjectStatus
from jose import jwt, JWTError
from app.core.config import settings

router = APIRouter()

def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return int(user_id)
    except JWTError:
        pass
    return None

@router.websocket("/chat/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: int, token: str = Query(...), db: Session = Depends(get_db)):
    user_id = get_user_from_token(token, db)
    if not user_id:
        await websocket.close(code=1008)
        return
        
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.status in [ProjectStatus.OPEN, ProjectStatus.CANCELLED]:
        await websocket.close(code=1008) # Policy Violation
        return
        
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Determine receiver (if client, then freelance; if freelance, then client)
            receiver_id = None
            if project.client_id == user_id:
                # Find the freelance who has the accepted proposal
                accepted = [p for p in project.proposals if p.status == "ACCEPTED"]
                if accepted:
                    receiver_id = accepted[0].freelance_id
            else:
                receiver_id = project.client_id
                
            if receiver_id:
                save_and_broadcast_message(db, project_id, user_id, receiver_id, data)
                await manager.send_personal_message(f"Msg: {data}", receiver_id)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
