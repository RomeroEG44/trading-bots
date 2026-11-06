@echo off
REM Doble clic para arrancar los bots y el panel (Windows).
cd /d "%~dp0"
call .venv\Scripts\activate
start "" http://localhost:8000
python -m tradingbots.motor
pause
