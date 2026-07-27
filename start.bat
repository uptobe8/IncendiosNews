@echo off
cd /d %~dp0
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install -q -r requirements.txt
python scripts\network_info.py
start "" http://127.0.0.1:8765
python server.py
