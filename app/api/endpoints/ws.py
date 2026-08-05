from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.websockets.manager import manager
from app.crud.crud_user import user as crud_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    # Verify user exists
    user = crud_user.get(db, id=user_id)
    if not user:
        await websocket.close(code=1008, reason="User not found")
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
            # For notifications, we mainly push data to the client
            pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
