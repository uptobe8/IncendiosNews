#!/usr/bin/env python3
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

UA = "Mozilla/5.0 (IncendiosNews/1.0; +https://github.com/uptobe8/IncendiosNews)"
OUT = Path(__file__).resolve().parents[1] / "data" / "latest.json"

MEDIA = [
    "EFE", "RTVE", "Europa Press", "El País", "EL PAÍS", "elDiario.es",
    "Cadena SER", "Onda Cero", "Telemadrid", "La Vanguardia", "20minutos",
    "ABC", "El Mundo"
]

QUERIES = [
    ("incendios Madrid Ávila Toledo when:1d", False),
    ("incendio Madrid when:1d", False),
    ("incendio Ávila when:1d", False),
    ("incendio Toledo when:1d", False),
    ("incendios carreteras Madrid Ávila Toledo when:1d", False),
    ("site:comunidad.madrid incendios Madrid when:2d", True),
    ("site:castillalamancha.es incendio Toledo when:2d", True),
    ("site:112.castillalamancha.es incendio Toledo when:7d", True),
    ("site:jcyl.es incendio Ávila when:2d", True),
    ("site:proteccioncivil.es incendios when:2d", True),
    ("site:dgt.es incendios Madrid Ávila Toledo when:2d", True),
]

TOWNS = {
    "Madrid": ["Navas del Rey", "Villa del Prado", "San Martín de Valdeiglesias", "Pelayos de la Presa", "Cenicientos", "Cadalso de los Vidrios", "Fresnedillas de la Oliva", "Navalagamella", "Aldea del Fresno", "Zarzalejo", "Robledo de Chavela", "Chapinería", "Colmenar de Arroyo", "Valdemaqueda", "Valdemorillo", "Quijorna", "El Escorial", "Pantano de San Juan", "Sierra Oeste"],
    "Ávila": ["Burgohondo", "Mijares", "Gavilanes", "Casavieja", "La Adrada", "Sotillo de la Adrada", "Piedralaves", "Navahondilla", "Casillas", "Santa María del Tiétar", "Hoyo de Pinares", "Villanueva de Ávila", "El Tiemblo", "Pedro Bernardo", "Higuera de las Dueñas", "Fresnedilla", "Cebreros", "Guisando", "Las Cruceras"],
    "Toledo": ["Almorox", "La Iglesuela del Tiétar", "El Real de San Vicente", "Castillo de Bayuela", "San Román de los Montes", "Almendral de la Cañada", "Sartajada", "Buenaventura", "Navamorcuende", "Pelahustán", "Garciotum", "Nuño Gómez", "Escalona"]
}

IMAGES = {
    "Madrid": "https://images.unsplash.com/photo-1523712999610-f77fbcfc3843?auto=format&fit=crop&w=1200&q=82",
    "Ávila": "https://images.unsplash.com/photo-1511497584788-876760111969?auto=format&fit=crop&w=1200&q=82",
    "Toledo": "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?auto=format&fit=crop&w=1200&q=82",
    "General": "https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?auto=format&fit=crop&w=1200&q=82",
    "official": "https://images.unsplash.com/photo-1582139329536-e7284fece509?auto=format&fit=crop&w=1200&q=82",
}

SOURCES = [
    {"name":"ASEM 112 / Comunidad de Madrid","kind":"official","area":"Madrid","url":"https://www.comunidad.madrid/seguridad-emergencias-asem-112"},
    {"name":"INFOCAL / Junta de Castilla y León","kind":"official","area":"Ávila","url":"https://medioambiente.jcyl.es/"},
    {"name":"INFOCAM / Castilla-La Mancha","kind":"official","area":"Toledo","url":"https://infocam.castillalamancha.es/"},
    {"name":"112 Castilla-La Mancha","kind":"official","area":"Toledo","url":"https://112.castillalamancha.es/"},
    {"name":"Protección Civil","kind":"official","area":"España","url":"https://www.proteccioncivil.es/"},
    {"name":"DGT","kind":"official","area":"Carreteras","url":"https://www.dgt.es/conoce-el-estado-del-trafico/"},
    {"name":"AEMET","kind":"official","area":"Meteorología","url":"https://www.aemet.es/"},
] + [{"name":n,"kind":"media","area":"España","url":""} for n in MEDIA]


def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def google_rss(query):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=es&gl=ES&ceid=ES:es"
    root = ET.fromstring(fetch(url))
    return root.findall("./channel/item")


def source_allowed(source, official):
    if official:
        return True
    s = (source or "").casefold()
    return any(m.casefold() in s for m in MEDIA)


def provinces_for(text):
    low = text.casefold()
    found = []
    for province, towns in TOWNS.items():
        if province.casefold() in low or any(t.casefold() in low for t in towns):
            found.append(province)
    return found or ["Madrid", "Ávila", "Toledo"]


def towns_for(text):
    low = text.casefold()
    result = []
    for province, towns in TOWNS.items():
        for town in towns:
            if town.casefold() in low and town not in result:
                result.append(town)
    return result[:5]


def item_from_xml(node, forced_official=False):
    title = clean_text(node.findtext("title"))
    link = clean_text(node.findtext("link"))
    description = clean_text(node.findtext("description"))
    source_node = node.find("source")
    source = clean_text(source_node.text if source_node is not None else "")
    if not title or not link or not source_allowed(source, forced_official):
        return None
    try:
        published_dt = parsedate_to_datetime(node.findtext("pubDate"))
        if published_dt.tzinfo is None:
            published_dt = published_dt.replace(tzinfo=timezone.utc)
        published = published_dt.isoformat()
    except Exception:
        published = datetime.now(timezone.utc).isoformat()
    text = f"{title} {description}"
    provinces = provinces_for(text)
    towns = towns_for(text)
    official = forced_official
    source_l = source.casefold()
    if any(k in source_l for k in ["comunidad de madrid", "castilla-la mancha", "junta de castilla", "protección civil", "dgt", "aemet", "112"]):
        official = True
    severity = "alert" if any(k in text.casefold() for k in ["evacua", "confin", "cortad", "alerta", "emergencia", "peligro", "activo", "sin estabilizar"]) else "info"
    display_province = " · ".join(provinces)
    image_key = provinces[0] if len(provinces) == 1 else "General"
    if official:
        image_key = "official"
    digest = hashlib.sha1((title + link).encode("utf-8")).hexdigest()[:16]
    return {
        "id": digest,
        "type": "official" if official else "news",
        "severity": severity,
        "province": display_province,
        "provinces": provinces,
        "town": " · ".join(towns) if towns else display_province,
        "published": published,
        "source": source or ("Fuente oficial" if official else "Medio"),
        "title": title,
        "summary": description[:420],
        "url": link,
        "image": IMAGES[image_key],
    }


def main():
    items = []
    errors = []
    seen = set()
    for query, official in QUERIES:
        try:
            for node in google_rss(query):
                item = item_from_xml(node, official)
                if not item:
                    continue
                key = re.sub(r"\W+", "", item["title"].casefold())[:180]
                if key in seen:
                    continue
                seen.add(key)
                items.append(item)
        except Exception as e:
            errors.append(f"{query}: {e}")
    items.sort(key=lambda x: x["published"], reverse=True)
    # El objetivo es una portada útil, no miles de duplicados del mismo directo.
    items = items[:120]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "sources": SOURCES,
        "errors": errors[:10],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardadas {len(items)} publicaciones; errores: {len(errors)}")


if __name__ == "__main__":
    main()
