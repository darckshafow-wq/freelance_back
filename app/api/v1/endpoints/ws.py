import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db
from app.services.websocket_manager import manager, save_and_broadcast_message
from app.models.project import Project, ProjectStatus, Proposal, ProposalStatus
from app.models.user import User, UserRole
from jose import jwt, JWTError
from app.core.config import settings

router = APIRouter()

def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user and user.is_active and not user.is_suspended:
            return user
    except JWTError:
        pass
    return None

@router.websocket("/chat/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    user = get_user_from_token(token, db)
    if not user:
        await websocket.close(code=1008)
        return

    # Vérification des droits d'accès au projet
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.status == ProjectStatus.CANCELLED:
        await websocket.close(code=1008)
        return

    # Trouver l'autre participant
    accepted_proposal = db.query(Proposal).filter(
        Proposal.project_id == project_id,
        Proposal.status == ProposalStatus.ACCEPTED
    ).first()

    # Fallback sur la première proposition si pas encore acceptée (phase interview)
    if not accepted_proposal:
        accepted_proposal = db.query(Proposal).filter(Proposal.project_id == project_id).first()

    if not accepted_proposal:
        await websocket.close(code=1008)
        return

    allowed_users = {project.client_id, accepted_proposal.freelance_id}
    if user.role != UserRole.ADMIN and user.id not in allowed_users:
        await websocket.close(code=1008)
        return

    # Déterminer le destinataire par défaut
    receiver_id = accepted_proposal.freelance_id if user.id == project.client_id else project.client_id

    await manager.connect(websocket, user.id)
    try:
        while True:
            # On s'attend à du JSON : {"type": "CHAT_MESSAGE", "content": "..."} ou {"type": "TYPING"}
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "CHAT_MESSAGE":
                content = data.get("content")
                if content:
                    msg = save_and_broadcast_message(db, project_id, user.id, receiver_id, content)
                    payload = {
                        "type": "NEW_MESSAGE",
                        "sender_id": user.id,
                        "content": content,
                        "created_at": str(msg.created_at)
                    }
                    await manager.send_json_to_user(payload, receiver_id)
                    await manager.send_json_to_user(payload, user.id)

            elif msg_type == "TYPING_START":
                await manager.send_json_to_user({"type": "PARTNER_TYPING", "typing": True}, receiver_id)

            elif msg_type == "TYPING_STOP":
                await manager.send_json_to_user({"type": "PARTNER_TYPING", "typing": False}, receiver_id)

    except WebSocketDisconnect:
        await manager.disconnect(websocket, user.id)
    except Exception as e:
        print(f"WS Error: {e}")
        await manager.disconnect(websocket, user.id)
