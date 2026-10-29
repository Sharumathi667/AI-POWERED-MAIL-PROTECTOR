import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BASE_DIR / ".env"
_DB_PATH = (_BASE_DIR / "data" / "investigation.db").as_posix()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_ENV_FILE, ".env"),
        extra="allow",
        env_file_encoding="utf-8"
    )

    PROJECT_NAME: str = "AI Phishing & Suspicious Login Investigation Platform"
    PROJECT_ID: str = "PS 1.3"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database (Robust absolute SQLite path)
    DATABASE_URL: str = f"sqlite:///{_DB_PATH}"
    
    # Environment & Demo Mode
    DEMO_MODE: bool = True
    ALLOW_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    # Authentication & Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/api/integrations/gmail/callback"
    FRONTEND_URL: str = "http://localhost:5173"
    SESSION_SECRET: str = "super_secure_shieldsoc_session_secret_key_2026"
    SESSION_COOKIE_NAME: str = "shieldsoc_session"
    SESSION_EXPIRE_HOURS: int = 24
    
    # Risk Engine Default Weights (0-100 normalized components)
    EMAIL_WEIGHT_CONTENT: float = 0.40
    EMAIL_WEIGHT_URL: float = 0.35
    EMAIL_WEIGHT_SENDER_HEADER: float = 0.25
    
    LOGIN_WEIGHT_LOCATION: float = 0.35
    LOGIN_WEIGHT_DEVICE: float = 0.30
    LOGIN_WEIGHT_AUTHENTICATION: float = 0.20
    LOGIN_WEIGHT_BEHAVIOR: float = 0.15
    
    # Correlation & Incidents
    CORRELATION_WINDOW_HOURS: int = 24
    MAX_CORRELATION_BONUS: float = 20.0
    
    # Severity Thresholds
    SEVERITY_LOW_MAX: int = 29
    SEVERITY_MED_MAX: int = 59
    SEVERITY_HIGH_MAX: int = 79
    # 80-100 is Critical
    
    # Artifact Paths (Absolute to avoid CWD sensitivity)
    EMAIL_MODEL_PATH: str = str(_BASE_DIR / "artifacts" / "email_model.joblib")
    EMAIL_METRICS_PATH: str = str(_BASE_DIR / "artifacts" / "email_metrics.json")
    LOGIN_MODEL_PATH: str = str(_BASE_DIR / "artifacts" / "login_model.joblib")
    LOGIN_METRICS_PATH: str = str(_BASE_DIR / "artifacts" / "login_metrics.json")

settings = Settings()
