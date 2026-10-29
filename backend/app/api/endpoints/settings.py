import os
import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.models.entities import SystemSetting, AuditLog

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdateSchema(BaseModel):
    email_weight_content: Optional[float] = None
    email_weight_url: Optional[float] = None
    email_weight_sender: Optional[float] = None
    login_weight_location: Optional[float] = None
    login_weight_device: Optional[float] = None
    login_weight_auth: Optional[float] = None
    correlation_window_hours: Optional[int] = None
    demo_mode: Optional[bool] = None

@router.get("")
def get_system_settings(db: Session = Depends(get_db)):
    return {
        "demo_mode": settings.DEMO_MODE,
        "project_name": settings.PROJECT_NAME,
        "project_id": settings.PROJECT_ID,
        "version": settings.VERSION,
        "database_url": settings.DATABASE_URL,
        "risk_weights": {
            "email_content": settings.EMAIL_WEIGHT_CONTENT,
            "email_url": settings.EMAIL_WEIGHT_URL,
            "email_sender_header": settings.EMAIL_WEIGHT_SENDER_HEADER,
            "login_location": settings.LOGIN_WEIGHT_LOCATION,
            "login_device": settings.LOGIN_WEIGHT_DEVICE,
            "login_authentication": settings.LOGIN_WEIGHT_AUTHENTICATION,
            "login_behavior": settings.LOGIN_WEIGHT_BEHAVIOR
        },
        "correlation": {
            "window_hours": settings.CORRELATION_WINDOW_HOURS,
            "max_bonus": settings.MAX_CORRELATION_BONUS
        },
        "severity_thresholds": {
            "low_max": settings.SEVERITY_LOW_MAX,
            "med_max": settings.SEVERITY_MED_MAX,
            "high_max": settings.SEVERITY_HIGH_MAX,
            "critical_min": settings.SEVERITY_HIGH_MAX + 1
        },
        "integrations": {
            "gmail_api": {
                "status": "Ready for Configuration (Demo Mode Active)",
                "mode": "Mode A (Synthetic Campus Data)",
                "oauth_configured": False,
                "note": "Production mode supports Google Workspace Administrator OAuth 2.0 with read-only scopes."
            },
            "identity_provider": {
                "status": "Simulated Active Directory / SAML SSO",
                "connected_domains": ["campus.edu"]
            }
        }
    }

@router.patch("")
def update_system_settings(update: SettingsUpdateSchema, db: Session = Depends(get_db)):
    if update.email_weight_content is not None:
        settings.EMAIL_WEIGHT_CONTENT = update.email_weight_content
    if update.email_weight_url is not None:
        settings.EMAIL_WEIGHT_URL = update.email_weight_url
    if update.email_weight_sender is not None:
        settings.EMAIL_WEIGHT_SENDER_HEADER = update.email_weight_sender
    if update.login_weight_location is not None:
        settings.LOGIN_WEIGHT_LOCATION = update.login_weight_location
    if update.login_weight_device is not None:
        settings.LOGIN_WEIGHT_DEVICE = update.login_weight_device
    if update.login_weight_auth is not None:
        settings.LOGIN_WEIGHT_AUTHENTICATION = update.login_weight_auth
    if update.correlation_window_hours is not None:
        settings.CORRELATION_WINDOW_HOURS = update.correlation_window_hours
    if update.demo_mode is not None:
        settings.DEMO_MODE = update.demo_mode
        
    audit = AuditLog(
        action="SYSTEM_SETTINGS_UPDATED",
        target_type="system",
        target_id="config",
        actor="Security Administrator",
        details=json.dumps(update.dict(exclude_none=True)),
        is_simulated=True
    )
    db.add(audit)
    db.commit()
    return {"message": "Settings updated successfully"}
