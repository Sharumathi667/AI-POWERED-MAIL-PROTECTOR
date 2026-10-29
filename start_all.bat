@echo off
echo ======================================================
echo   Launching ShieldSOC Backend + Frontend
echo ======================================================
cd /d %~dp0

start "ShieldSOC Backend (FastAPI)" cmd /k "run_backend.bat"
start "ShieldSOC Frontend (React/Vite)" cmd /k "run_frontend.bat"

echo.
echo Both servers have been launched in separate windows!
echo Frontend will be ready at: http://localhost:5173
echo.

