import json
from fastapi import WebSocket
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.models.message import Message

class ConnectionManager:
    def __init__(self):
        # Maps user_id to a list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        # Diffuser le statut en ligne (optionnel, selon les besoins UI)
        await self.broadcast_presence(user_id, True)

    async def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                await self.broadcast_presence(user_id, False)

    def is_online(self, user_id: int) -> bool:
        return user_id in self.active_connections

    async def send_json_to_user(self, data: Dict[str, Any], user_id: int):
        """Envoie un message JSON à toutes les sessions d'un utilisateur"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(data)
                except:
                    # Gérer les connexions rompues silencieusement
                    pass

    async def broadcast_presence(self, user_id: int, online: bool):
        """Notifie le changement de statut (pourrait être filtré par contacts)"""
        # Cette implémentation est basique, en production on filtrerait
        pass

manager = ConnectionManager()

def save_and_broadcast_message(db: Session, project_id: int, sender_id: int, receiver_id: int, content: str) -> Message:
    # Persist message
    msg = Message(
        project_id=project_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
