#!/bin/bash
cd "$(dirname "$0")"
PY="python3"
command -v python3 >/dev/null 2>&1 || PY="python"
$PY -m pip install -q -r requirements.txt
( sleep 2; open "http://127.0.0.1:8000" ) >/dev/null 2>&1 &
$PY server.py
