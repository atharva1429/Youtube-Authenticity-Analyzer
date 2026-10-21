@echo off
cd /d "%~dp0"
start "Backend" cmd /k "uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
cd frontend
start "Frontend" cmd /k "npm run dev"
