@echo off
set "PATH=C:\Users\koosh\AppData\Local\Programs\Python\Python312;%PATH%"
cd /d "%~dp0"
echo Starting Instrument Designer Backend on port 8000...
python -m uvicorn backend.server:app --port 8000 --reload
pause
