from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.services.ai import ai_service

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health_check():
    return {"status": "ok", "service": "CareFlow AI Backend"}


@router.get("/db")
def db_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@router.get("/ai")
async def ai_health_check():
    is_healthy = await ai_service.health_check()
    return {"status": "ok" if is_healthy else "unavailable", "service": "Ollama AI"}
