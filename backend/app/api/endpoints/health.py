import datetime
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "project_id": settings.PROJECT_ID,
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
