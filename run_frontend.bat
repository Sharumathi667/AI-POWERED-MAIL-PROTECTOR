@echo off
echo ======================================================
echo   Installing Dependencies and Starting Frontend (Port 5173)
echo ======================================================
cd /d %~dp0frontend
call npm install
call npm run dev
pause

