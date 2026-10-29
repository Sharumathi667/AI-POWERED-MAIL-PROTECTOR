import datetime
import httpx
import jwt
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.models.entities import User, AuditLog

class AuthService:
    @staticmethod
    def create_session_token(user: User) -> str:
        """Create a signed JWT session token with expiration and claims."""
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=settings.SESSION_EXPIRE_HOURS)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.full_name or user.username,
            "role": user.role,
            "picture": user.picture_url or "",
            "exp": expire,
            "iat": datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SESSION_SECRET, algorithm="HS256")
        return token

    @staticmethod
    def decode_session_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate session token signature and expiration."""
        try:
            payload = jwt.decode(token, settings.SESSION_SECRET, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError:
            return None

    @staticmethod
    async def exchange_google_code(code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Google authorization code for access and ID tokens."""
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=400,
                detail="Google OAuth credentials are not configured in backend .env. Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            )

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(token_url, data=data)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Google token exchange failed: {resp.text}"
                )
            return resp.json()

    @staticmethod
    async def verify_google_id_token(id_token: str) -> Dict[str, Any]:
        """Verify Google ID token via Google's tokeninfo API."""
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(verify_url)
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Google ID token signature or expired token"
                )
            payload = resp.json()

            # Verify audience if client ID is set
            if settings.GOOGLE_CLIENT_ID and payload.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=401,
                    detail="Google ID token audience (aud) mismatch"
                )

            # Verify issuer
            iss = payload.get("iss")
            if iss not in ["accounts.google.com", "https://accounts.google.com"]:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Google token issuer"
                )

            return payload

auth_service = AuthService()

def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Extract authenticated user from session cookie or Authorization Bearer header if present."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return None

    payload = auth_service.decode_session_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    return user

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Enforce authentication; raises 401 if unauthenticated."""
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required. Please sign in.")
    return user
