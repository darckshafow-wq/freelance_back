"""
==========================================================
  main.py — Point d'entrée du Backend Freelance Platform
==========================================================

Ce fichier configure :
  1. L'application FastAPI avec CORS
  2. Le routage API (REST + WebSocket)
  3. Le système d'alertes d'erreurs (log fichier + email)
"""

import logging
import traceback
from logging.handlers import SMTPHandler

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.api.endpoints.ws import router as ws_router
from app.core.config import settings

# ─── Création de l'application ──────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# ─── CORS : autorise l'accès depuis les origines configurées ───────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        # Flutter web dev server (port dynamique) — on autorise tout localhost
        "http://localhost:53936",
        "http://localhost:53937",
        "http://localhost:53938",
        "http://localhost:53939",
        "http://localhost:53940",
        "http://localhost:53941",
        "http://localhost:53942",
        "http://localhost:53943",
        "http://localhost:53944",
        "http://localhost:53945",
        "http://localhost:51000",
        "http://localhost:52000",
        "http://localhost:54000",
        "http://localhost:40820",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes REST (préfixées /api/v1) ────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)

# ─── Route WebSocket (montée directement sur /ws, pas sous /api/v1)──
# Le frontend Flutter se connecte à ws://<host>/ws/<userId>
app.include_router(ws_router, prefix="/ws", tags=["websockets"])

# ─── Route de santé ─────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": "Welcome to Freelance_p Backend API"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}


# ====================================================================
# SYSTÈME D'ALERTES D'ERREURS (Log fichier + Email)
# ====================================================================

# --- Paramètres SMTP ---
# NOTE: En production, ces valeurs doivent venir du .env
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USER = settings.SMTP_USER
SMTP_PASSWORD = settings.SMTP_PASSWORD
ADMIN_EMAILS = settings.ADMIN_EMAILS

# --- Configuration du Logger ---
logger = logging.getLogger("api_error_logger")
logger.setLevel(logging.ERROR)

# 1. Handler fichier : écrit toutes les erreurs dans api_errors.log
file_handler = logging.FileHandler("api_errors.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

# 2. Handler email : envoie un mail à l'admin pour chaque erreur 500
if SMTP_USER and SMTP_PASSWORD and ADMIN_EMAILS:
    try:
        mail_handler = SMTPHandler(
            mailhost=(SMTP_HOST, SMTP_PORT),
            fromaddr=SMTP_USER,
            toaddrs=ADMIN_EMAILS,
            subject="[URGENT] Erreur 500 sur Freelance_p API",
            credentials=(SMTP_USER, SMTP_PASSWORD),
            secure=(),  # Active TLS
        )
        mail_handler.setFormatter(
            logging.Formatter(
                """
    ── Erreur API ──────────────────────────
    Message : %(message)s
    Heure   : %(asctime)s
    ────────────────────────────────────────
    """
            )
        )
        logger.addHandler(mail_handler)
    except Exception as e:
        # Si la config SMTP échoue, on log en console mais on ne plante pas
        print(f"⚠️  Configuration SMTP échouée (emails désactivés) : {e}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation failed",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ─── Exception Handler Global ───────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Intercepte TOUTES les exceptions non gérées.
    → Log dans api_errors.log
    → Envoi d'un email d'alerte à l'admin
    → Retourne une réponse 500 propre à l'utilisateur
    """
    error_msg = f"Erreur non gérée sur {request.method} {request.url}\n"
    error_msg += "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )

    # Enregistre dans le fichier ET envoie l'email
    logger.error(error_msg)

    # Réponse propre au client (pas de stack trace exposée)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Une erreur interne est survenue. L'administrateur a été notifié."
        },
    )
