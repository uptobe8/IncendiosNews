@echo off
cd /d "%~dp0"
py -m pip install -q -r requirements.txt 2>nul || python -m pip install -q -r requirements.txt
start "" http://127.0.0.1:8000
py server.py 2>nul || python server.py
pause
