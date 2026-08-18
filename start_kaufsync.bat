@echo off
echo Starte KaufSync Server...

:: Backend in einem neuen Fenster starten
start "KaufSync Backend" cmd /k "cd backend && call .\venv\Scripts\activate.bat && uvicorn main:app --reload"

:: Frontend in einem neuen Fenster starten
start "KaufSync Frontend" cmd /k "cd frontend && npm run dev"