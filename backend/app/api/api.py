from fastapi import APIRouter
from backend.app.api.endpoints import (
    health, auth, integrations, dashboard, emails, logins, incidents, actions, models, audit, settings
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(integrations.router)
api_router.include_router(dashboard.router)
api_router.include_router(emails.router)
api_router.include_router(logins.router)
api_router.include_router(incidents.router)
api_router.include_router(actions.router)
api_router.include_router(models.router)
api_router.include_router(audit.router)
api_router.include_router(settings.router)
