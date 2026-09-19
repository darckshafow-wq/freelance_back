from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Configuration équilibrée pour 4 workers et max_connections=1000 sur Postgres
# 4 workers * (100 pool + 100 overflow) = 800 connections max
engine_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    # Paramètres optimisés pour Postgres
    engine_args.update({
        "pool_size": 100,        # 100 connexions de base par worker
        "max_overflow": 100,    # 100 de plus en cas de pic
        "pool_timeout": 60,     # Attente avant erreur
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    })

engine = create_engine(settings.DATABASE_URL, **engine_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
