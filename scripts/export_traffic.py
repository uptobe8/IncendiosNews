from __future__ import annotations

import json
from pathlib import Path

from traffic import refresh_dgt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "traffic.json"


def main():
    payload = refresh_dgt(True)
    incidents = payload.get("incidents", [])

    # Fail closed. The national DGT incident feed should contain many records.
    # If parsing returns only a handful, it is not safe to infer that a route is clear.
    if payload.get("ok") and len(incidents) < 10:
        payload["ok"] = False
        payload["stale"] = True
        payload["error"] = "incomplete_dgt_dataset"
        payload["coverage_warning"] = (
            "El fichero DGT se descargó, pero no se han podido interpretar suficientes "
            "incidencias para verificar rutas con seguridad."
        )

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
    print(
        f"DGT: ok={payload.get('ok')} incidencias={len(incidents)} "
        f"checked_at={payload.get('checked_at')}"
    )


if __name__ == "__main__":
    main()
