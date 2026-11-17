from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict:
    """The process is up. Used later as the Kubernetes liveness probe."""
    return {"status": "ok"}


@router.get("/ready")
def ready(response: Response) -> dict:
    """The database is reachable and pgvector is installed. Used later as the readiness probe."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            has_vector = conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ).first() is not None
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "down"}

    if not has_vector:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "up", "pgvector": False}

    return {"status": "ok", "database": "up", "pgvector": True}
