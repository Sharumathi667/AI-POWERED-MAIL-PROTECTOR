import json
import urllib.parse
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.models.entities import User, AuditLog
from backend.app.services.auth_service import get_current_user_optional, get_current_user, auth_service
from backend.app.services.gmail_sync_service import sync_user_gmail

router = APIRouter(prefix="/integrations", tags=["Integrations"])

def _is_google_configured() -> bool:
    cid = (settings.GOOGLE_CLIENT_ID or "").strip()
    sec = (settings.GOOGLE_CLIENT_SECRET or "").strip()
    if not cid or not sec:
        return False
    lower_cid = cid.lower()
    lower_sec = sec.lower()
    return not ("your_google" in lower_cid or "your_" in lower_cid or "placeholder" in lower_cid or "your_google" in lower_sec or "your_" in lower_sec)

@router.get("/status")
def get_integrations_status(
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Returns integration status for Gmail and Identity Provider."""
    is_google_configured = _is_google_configured()

    return {
        "google_oauth": {
            "configured": is_google_configured,
            "client_id_set": bool(settings.GOOGLE_CLIENT_ID),
            "redirect_uri": settings.GOOGLE_REDIRECT_URI
        },
        "gmail": {
            "mode": "Mode B (Gmail API Read-Only)" if (user and user.gmail_connected) else "Mode A (Synthetic Campus Data)",
            "connected": bool(user and user.gmail_connected),
            "connected_email": user.email if (user and user.gmail_connected) else None,
            "scope": "https://www.googleapis.com/auth/gmail.readonly",
            "redirect_uri": settings.GMAIL_REDIRECT_URI,
            "access_type": "Read-Only (Inspecting headers & subjects for security analysis)"
        },
        "identity_provider": {
            "name": "Campus Active Directory / SAML SSO",
            "status": "Operational (Simulated Telemetry)",
            "domains": ["campus.edu"]
        }
    }

@router.get("/gmail/connect")
def connect_gmail(
    user: User = Depends(get_current_user)
):
    """Generates Gmail OAuth consent URL requesting read-only mailbox permissions."""
    if not _is_google_configured():
        raise HTTPException(
            status_code=400,
            detail="Google OAuth is not configured. Please add valid GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to backend/.env."
        )

    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "state": f"user_{user.id}"
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return {"url": url}

@router.get("/gmail/callback")
async def gmail_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Callback for Gmail API OAuth consent."""
    if error:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/emails?error={urllib.parse.quote(error)}")

    if not code or not state or not state.startswith("user_"):
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/emails?error=invalid_state")

    try:
        user_id = int(state.replace("user_", ""))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/emails?error=user_not_found")

        tokens = await auth_service.exchange_google_code(code, settings.GMAIL_REDIRECT_URI)
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        user.gmail_connected = True
        user.gmail_access_token = access_token
        if refresh_token:
            user.gmail_refresh_token = refresh_token

        audit = AuditLog(
            action="GMAIL_API_CONNECTED",
            target_type="user",
            target_id=str(user.id),
            actor=user.email,
            details=json.dumps({"scope": "gmail.readonly", "status": "authorized"}),
            is_simulated=False
        )
        db.add(audit)
        db.commit()

        # Immediate sync
        try:
            await sync_user_gmail(user, db, max_results=30)
        except Exception as e:
            print(f"[Initial Sync in Callback Error]: {e}")

        return RedirectResponse(url=f"{settings.FRONTEND_URL}/emails?status=gmail_connected")

    except Exception as e:
        print(f"[Gmail Callback Error]: {e}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/emails?error={urllib.parse.quote(str(e))}")

@router.post("/gmail/disconnect")
def disconnect_gmail(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnects Gmail integration and clears stored tokens."""
    user.gmail_connected = False
    user.gmail_access_token = None
    user.gmail_refresh_token = None

    audit = AuditLog(
        action="GMAIL_API_DISCONNECTED",
        target_type="user",
        target_id=str(user.id),
        actor=user.email,
        details=json.dumps({"status": "disconnected"}),
        is_simulated=False
    )
    db.add(audit)
    db.commit()

    return {"message": "Gmail integration disconnected successfully", "connected": False}
