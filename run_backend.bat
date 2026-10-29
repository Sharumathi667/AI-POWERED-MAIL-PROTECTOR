@echo off
echo ======================================================
echo   Starting ShieldSOC FastAPI Backend (Port 8000)
echo ======================================================
cd /d %~dp0
python -c "import fastapi, sqlalchemy" 2>nul || (
    echo Installing backend dependencies...
    python -m pip install -r backend/requirements.txt
)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
