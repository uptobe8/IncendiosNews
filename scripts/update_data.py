from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "latest.json"

OFFICIAL_DOMAINS = {
    "comunidad.madrid": "Comunidad de Madrid",
    "madrid.org": "Comunidad de Madrid",
    "jcyl.es": "Junta de Castilla y León",
    "datosabiertos.jcyl.es": "Junta de Castilla y León",
    "castillalamancha.es": "Gobierno de Castilla-La Mancha",
    "infocam.castillalamancha.es": "INFOCAM Castilla-La Mancha",
    "proteccioncivil.es": "Protección Civil",
    "interior.gob.es": "Ministerio del Interior",
    "dgt.es": "DGT",
    "aemet.es": "AEMET",
    "defensa.gob.es": "Ministerio de Defensa",
}

MEDIA_SOURCES = [
    "EFE", "RTVE", "Europa Press", "Cadena SER", "Onda Cero", "Telemadrid",
    "Diario de Ávila", "La Tribuna de Toledo", "ABC", "El País", "El Mundo",
    "La Vanguardia", "20minutos", "eldiario.es", "El Español"
]

QUERIES = [
    'incendio Madrid',
    'incendio Ávila',
    'incendio Toledo',
    'incendio forestal Madrid Ávila Toledo',
    'evacuación incendio Madrid Ávila Toledo',
    'confinamiento incendio Madrid Ávila Toledo',
    'carreteras incendio Madrid Ávila Toledo',
    'site:comunidad.madrid incendio',
    'site:jcyl.es incendio Ávila',
    'site:castillalamancha.es incendio Toledo',
    'site:proteccioncivil.es incendio Madrid Ávila Toledo',
    'site:dgt.es incendio Madrid Ávila Toledo',
]

UA = "IncendiosNews/1.0 (+https://github.com/uptobe8/IncendiosNews)"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml,application/xml,text/xml,*/*"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def clean(text: str | None) -> str:
    text = text or ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def province_for(text: str) -> str:
    low = text.lower()
    if "ávila" in low or "avila" in low:
        return "Ávila"
    if "toledo" in low:
        return "Toledo"
    return "Madrid"


def parse_date(text: str | None) -> str:
    if not text:
        return datetime.now(timezone.utc).isoformat()
    try:
        d = parsedate_to_datetime(text)
        if not d.tzinfo:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def domain_from_url(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def is_official(source_url: str) -> tuple[bool, str | None]:
    dom = domain_from_url(source_url)
    for allowed, label in OFFICIAL_DOMAINS.items():
        if dom == allowed or dom.endswith("." + allowed):
            return True, label
    return False, None


def google_news(query: str) -> list[dict]:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query,
        "hl": "es",
        "gl": "ES",
        "ceid": "ES:es",
    })
    root = ET.fromstring(fetch(url))
    rows = []
    for item in root.findall("./channel/item"):
        title = clean(item.findtext("title"))
        link = clean(item.findtext("link"))
        desc = clean(item.findtext("description"))
        published = parse_date(item.findtext("pubDate"))
        src = item.find("source")
        source_name = clean(src.text if src is not None else "")
        source_url = clean(src.attrib.get("url", "") if src is not None else "")
        official, official_name = is_official(source_url)
        text = f"{title} {desc}"
        if not any(k in text.lower() for k in ["incend", "fuego", "evacua", "confin", "humo", "forestal"]):
            continue
        rows.append({
            "id": re.sub(r"[^a-zA-Z0-9]+", "-", (source_name + "-" + title).lower())[:120],
            "type": "official" if official else "news",
            "severity": "alert" if official else "info",
            "province": province_for(text),
            "town": province_for(text),
            "published": published,
            "source": official_name or source_name or "Medio verificado",
            "source_url": source_url,
            "title": title,
            "summary": desc[:420],
            "url": link,
        })
    return rows


def main() -> None:
    items: list[dict] = []
    seen = set()
    errors = []
    for q in QUERIES:
        try:
            for row in google_news(q):
                key = (row["title"].lower(), row["source"].lower())
                if key in seen:
                    continue
                seen.add(key)
                items.append(row)
        except Exception as e:
            errors.append(f"{q}: {type(e).__name__}")

    items.sort(key=lambda x: x["published"], reverse=True)
    official_sources = [
        {"name": "ASEM 112 / Comunidad de Madrid", "kind": "official", "area": "Madrid", "url": "https://www.comunidad.madrid/servicios/seguridad-emergencias"},
        {"name": "INFOCAL / Junta de Castilla y León", "kind": "official", "area": "Ávila", "url": "https://medioambiente.jcyl.es/"},
        {"name": "INFOCAM / Castilla-La Mancha", "kind": "official", "area": "Toledo", "url": "https://infocam.castillalamancha.es/"},
        {"name": "Protección Civil", "kind": "official", "area": "España", "url": "https://www.proteccioncivil.es/"},
        {"name": "DGT", "kind": "official", "area": "Carreteras", "url": "https://www.dgt.es/conoce-el-estado-del-trafico/"},
        {"name": "AEMET", "kind": "official", "area": "Meteorología", "url": "https://www.aemet.es/"},
    ]
    media_sources = [{"name": n, "kind": "media", "area": "España", "url": ""} for n in MEDIA_SOURCES]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": items[:160],
        "sources": official_sources + media_sources,
        "errors": errors,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
