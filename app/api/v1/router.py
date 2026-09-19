from fastapi import APIRouter
from app.api.v1.endpoints import auth, client, freelance, admin, review, users, ws, messages, notifications, upload, locations

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(client.router, prefix="/client", tags=["client"])
api_router.include_router(freelance.router, prefix="/freelance", tags=["freelance"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(review.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(messages.router, prefix="/projects", tags=["messages"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
