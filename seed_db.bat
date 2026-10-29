@echo off
echo ======================================================
echo   1. Checking and Installing Backend Dependencies
echo ======================================================
cd /d %~dp0
python -m pip install -r backend/requirements.txt

echo.
echo ======================================================
echo   2. Initializing and Seeding ShieldSOC Database
echo ======================================================
python backend/scripts/seed_database.py
echo.
pause
