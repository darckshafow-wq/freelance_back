from fastapi import APIRouter

# Importations de base
from app.api.endpoints import auth, users

# Importation spécifique du routeur freelance depuis son sous-dossier
from app.api.endpoints.freelance.freelance import router as freelance_router
from app.api.endpoints.client.client import router as client_router
from app.api.endpoints.admin.admin import router as admin_router
from app.api.endpoints import ws

api_router = APIRouter()

# ─── CORE AUTH & UTILISATEURS ──────────────────────────────────────────
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# ─── ESPACE UNIQUE DU FREELANCE ───────────────────────────────────────────
# Expose toutes nos routes optimisées (/tasks, /apply, /conversations, /messages, /stats, etc.)
api_router.include_router(freelance_router, prefix="/freelance", tags=["freelance"])

# ─── AUTRES RÔLES ET WEBSOCKETS ───────────────────────────────────────────
api_router.include_router(client_router, prefix="/client", tags=["client"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(ws.router, prefix="/ws", tags=["websockets"])