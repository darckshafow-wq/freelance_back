from app.api.endpoints import users, auth, tasks, applications, admin, dashboard, ws, messages, statistics, reviews
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(ws.router, prefix="/ws", tags=["websockets"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
