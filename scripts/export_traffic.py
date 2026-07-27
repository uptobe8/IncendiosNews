from __future__ import annotations

import json
from pathlib import Path

from traffic import refresh_dgt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "traffic.json"


def main():
    payload = refresh_dgt(True)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    print(f"DGT: ok={payload.get('ok')} incidencias={len(payload.get('incidents', []))} checked_at={payload.get('checked_at')}")


if __name__ == "__main__":
    main()
