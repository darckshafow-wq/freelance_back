from fastapi import APIRouter
from app.api.v1.endpoints import auth, client, freelance, admin, review, ws

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(client.router, prefix="/client", tags=["client"])
api_router.include_router(freelance.router, prefix="/freelance", tags=["freelance"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(review.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
