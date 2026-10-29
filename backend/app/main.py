import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.database.session import engine, Base
from backend.app.api.api import api_router
from backend.app.ml.email_classifier import email_classifier
from backend.app.ml.login_detector import login_detector

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    print("[Startup] Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify/Load ML models
    print("[Startup] Loading Machine Learning model artifacts...")
    email_classifier.load_model()
    login_detector.load_model()
    print("[Startup] System is ready and healthy!")
    yield
    print("[Shutdown] Shutting down application gracefully.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Phishing Email and Suspicious Login Investigation Challenge (PS 1.3)",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware supporting credentials for localhost / 127.0.0.1
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "documentation": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
