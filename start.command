#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -q -r requirements.txt
python scripts/network_info.py
python server.py &
PID=$!
sleep 2
open http://127.0.0.1:8765
wait $PID
