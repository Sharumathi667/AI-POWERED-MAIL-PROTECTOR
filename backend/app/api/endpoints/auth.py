import json
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, Response, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.models.entities import User, AuditLog
from backend.app.services.auth_service import (
    auth_service, get_current_user_optional, get_current_user
)
from backend.app.services.gmail_sync_service import sync_user_gmail

router = APIRouter(prefix="/auth", tags=["Authentication"])

class GoogleTokenLoginRequest(BaseModel):
    credential: str # Google ID token from Google Identity Services

class DemoLoginRequest(BaseModel):
    role: Optional[str] = "analyst"

def is_google_oauth_configured() -> bool:
    cid = (settings.GOOGLE_CLIENT_ID or "").strip()
    sec = (settings.GOOGLE_CLIENT_SECRET or "").strip()
    if not cid or not sec:
        return False
    lower_cid = cid.lower()
    lower_sec = sec.lower()
    if "your_google" in lower_cid or "your_" in lower_cid or "placeholder" in lower_cid:
        return False
    if "your_google" in lower_sec or "your_" in lower_sec or "placeholder" in lower_sec:
        return False
    return True

@router.get("/config")
def get_auth_config():
    """Returns Google OAuth client configuration status."""
    is_configured = is_google_oauth_configured()
    return {
        "is_google_configured": is_configured,
        "google_client_id": settings.GOOGLE_CLIENT_ID if is_configured else "",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "demo_mode": settings.DEMO_MODE,
        "setup_guide": {
            "steps": [
                "1. Open Google Cloud Console: https://console.cloud.google.com/",
                "2. Create or select a project and configure the OAuth consent screen",
                "3. Create OAuth 2.0 Client ID (Web Application)",
                "4. Add Authorized JavaScript origin: http://localhost:5173",
                "5. Add Authorized redirect URI: http://localhost:8000/api/auth/google/callback",
                "6. Add Gmail Authorized redirect URI: http://localhost:8000/api/integrations/gmail/callback",
                "7. Save GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env"
            ]
        }
    }

@router.get("/google/url")
def get_google_auth_url():
    """Generates the Google OAuth 2.0 authorization URL requesting profile and Gmail read-only scopes."""
    if not is_google_oauth_configured():
        raise HTTPException(
            status_code=400,
            detail="Google OAuth is not configured. Please set valid GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env."
        )

    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent select_account",
        "state": "shieldsoc_auth_state"
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return {"url": url}

@router.get("/google/callback")
async def google_auth_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Callback endpoint for Google OAuth authorization code flow."""
    if error:
        redirect_target = f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote(error)}"
        return RedirectResponse(url=redirect_target)

    if not code:
        redirect_target = f"{settings.FRONTEND_URL}/login?error=no_code_provided"
        return RedirectResponse(url=redirect_target)

    try:
        # Exchange code for token
        tokens = await auth_service.exchange_google_code(code, settings.GOOGLE_REDIRECT_URI)
        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not id_token:
            raise HTTPException(status_code=400, detail="Missing id_token in Google response")

        user_info = await auth_service.verify_google_id_token(id_token)
        google_sub = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name", email.split("@")[0] if email else "User")
        picture = user_info.get("picture", "")

        # Upsert user in database
        user = db.query(User).filter(
            (User.google_sub == google_sub) | (User.email == email)
        ).first()

        if user:
            user.google_sub = google_sub
            user.full_name = name
            user.picture_url = picture
            if access_token:
                user.gmail_connected = True
                user.gmail_access_token = access_token
            if refresh_token:
                user.gmail_refresh_token = refresh_token
        else:
            username = email.split("@")[0]
            base_un = username
            count = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_un}_{count}"
                count += 1

            user = User(
                username=username,
                email=email,
                full_name=name,
                google_sub=google_sub,
                picture_url=picture,
                gmail_connected=bool(access_token),
                gmail_access_token=access_token,
                gmail_refresh_token=refresh_token,
                role="admin" if "admin" in email else "analyst",
                is_active=True
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        # Trigger immediate background sync of real Gmail emails
        if user.gmail_access_token:
            try:
                await sync_user_gmail(user, db, max_results=30)
            except Exception as sync_err:
                print(f"[Initial Gmail Sync Warning]: {sync_err}")

        # Create session token
        session_token = auth_service.create_session_token(user)

        # Record audit log
        audit = AuditLog(
            action="USER_LOGIN_GOOGLE_OAUTH",
            target_type="user",
            target_id=str(user.id),
            actor=user.email,
            details=json.dumps({"google_sub": google_sub, "name": name, "gmail_connected": user.gmail_connected}),
            is_simulated=False
        )
        db.add(audit)
        db.commit()

        # Redirect to frontend dashboard and set HTTP-only cookie
        redirect_target = f"{settings.FRONTEND_URL}/emails"
        response = RedirectResponse(url=redirect_target, status_code=302)
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            samesite="lax",
            max_age=settings.SESSION_EXPIRE_HOURS * 3600,
            path="/"
        )
        return response

    except Exception as e:
        print(f"[Google Auth Error]: {e}")
        redirect_target = f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote(str(e))}"
        return RedirectResponse(url=redirect_target)

@router.post("/google/token")
async def google_token_login(
    payload: GoogleTokenLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Google Identity Services token authentication endpoint."""
    user_info = await auth_service.verify_google_id_token(payload.credential)
    google_sub = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name", email.split("@")[0] if email else "User")
    picture = user_info.get("picture", "")

    user = db.query(User).filter(
        (User.google_sub == google_sub) | (User.email == email)
    ).first()

    if user:
        user.google_sub = google_sub
        user.full_name = name
        user.picture_url = picture
    else:
        user = User(
            username=email.split("@")[0],
            email=email,
            full_name=name,
            google_sub=google_sub,
            picture_url=picture,
            role="analyst",
            is_active=True
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    session_token = auth_service.create_session_token(user)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        path="/"
    )

    audit = AuditLog(
        action="USER_LOGIN_GOOGLE_GIS",
        target_type="user",
        target_id=str(user.id),
        actor=user.email,
        details=json.dumps({"google_sub": google_sub}),
        is_simulated=False
    )
    db.add(audit)
    db.commit()

    return {
        "is_authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "picture_url": user.picture_url,
            "gmail_connected": user.gmail_connected
        }
    }

@router.post("/demo-login")
def demo_analyst_login(
    payload: DemoLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Development/Demo login bypass allowing evaluation when Google OAuth keys are not yet configured."""
    role = payload.role or "analyst"
    email = f"{role}@campus.edu"
    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            username=role,
            email=email,
            full_name=f"Lead SOC {role.capitalize()}",
            role=role,
            picture_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    session_token = auth_service.create_session_token(user)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        path="/"
    )

    audit = AuditLog(
        action="USER_LOGIN_DEMO_BYPASS",
        target_type="user",
        target_id=str(user.id),
        actor=user.email,
        details=json.dumps({"role": role, "note": "Local evaluation mode active"}),
        is_simulated=True
    )
    db.add(audit)
    db.commit()

    return {
        "is_authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "picture_url": user.picture_url,
            "gmail_connected": user.gmail_connected
        }
    }

@router.get("/me")
def get_current_user_profile(
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Returns profile of currently authenticated user, or is_authenticated: false."""
    if not user:
        return {"is_authenticated": False, "user": None}

    return {
        "is_authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name or user.username,
            "role": user.role,
            "picture_url": user.picture_url,
            "gmail_connected": user.gmail_connected
        }
    }

@router.post("/logout")
def logout_user(
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Logs out current user and clears session cookie."""
    if user:
        audit = AuditLog(
            action="USER_LOGOUT",
            target_type="user",
            target_id=str(user.id),
            actor=user.email,
            details=json.dumps({"status": "logged_out"}),
            is_simulated=False
        )
        db.add(audit)
        db.commit()

    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
    return {"message": "Successfully logged out", "is_authenticated": False}
