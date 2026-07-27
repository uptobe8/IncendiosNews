from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seed.json"
OUT = ROOT / "data" / "feed.json"
MADRID_TZ = ZoneInfo("Europe/Madrid")

ALLOWED = {
    "efe", "rtve", "europa press", "cadena ser", "onda cero", "telemadrid",
    "diario de ávila", "tribuna de ávila", "la tribuna de toledo", "el país",
    "abc", "la vanguardia", "el español", "madrid actual", "20minutos",
    "el mundo", "la razón", "castilla-la mancha media"
}

TOWNS = {
    "Madrid": [
        "San Martín de Valdeiglesias", "Villa del Prado", "Pelayos de la Presa",
        "Chapinería", "Navas del Rey", "Cenicientos", "Aldea del Fresno",
        "Valdemaqueda", "Robledo de Chavela", "Zarzalejo", "Navalagamella",
        "Colmenar del Arroyo", "Fresnedillas de la Oliva", "Valdemorillo", "Quijorna"
    ],
    "Ávila": [
        "Burgohondo", "Sotillo de la Adrada", "Piedralaves", "La Adrada",
        "Casavieja", "Mijares", "Navaluenga", "El Tiemblo", "Higuera de las Dueñas",
        "Gavilanes", "Fresnedilla", "Navahondilla", "Hoyo de Pinares", "Cebreros",
        "Casillas", "Santa María del Tiétar", "Pedro Bernardo"
    ],
    "Toledo": [
        "Almorox", "La Iglesuela del Tiétar", "Sartajada", "Almendral de la Cañada",
        "Buenaventura", "Navamorcuende", "El Real de San Vicente", "Hinojosa de San Vicente",
        "Castillo de Bayuela", "Garciotum", "Nuñogómez", "Pelahustán", "San Román de los Montes"
    ],
}

FIRE_RE = re.compile(
    r"incendi|fuego|evacu|desaloj|confin|carretera|corte|dgt|esalert|humo|ume|quemad|extinci|emergencia",
    re.I,
)

TARGET_TERMS = ["Madrid", "Ávila", "Avila", "Toledo", "Sierra Oeste", "Burgohondo", "Almorox"]
for province_towns in TOWNS.values():
    TARGET_TERMS.extend(province_towns)
TARGET_RE = re.compile("|".join(re.escape(x) for x in sorted(set(TARGET_TERMS), key=len, reverse=True)), re.I)

GOOGLE_QUERIES = [
    "incendio Madrid Ávila Toledo when:1d",
    "incendio Sierra Oeste Madrid when:1d",
    "incendio Burgohondo Ávila when:1d",
    "incendio Almorox Toledo when:1d",
    "carreteras cortadas incendio Madrid Ávila Toledo when:1d",
    "evacuación incendio Madrid Ávila Toledo when:1d",
    "confinamiento incendio Madrid Ávila Toledo when:1d",
]


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)).strip()


def ident(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:18]


def parse_pub(value: str | None):
    if not value:
        return None
    try:
        d = parsedate_to_datetime(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(MADRID_TZ).isoformat(timespec="seconds")
    except Exception:
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(MADRID_TZ).isoformat(timespec="seconds")
    except Exception:
        return None


def get(url: str, **kwargs):
    return requests.get(
        url,
        headers={
            "User-Agent": "IncendiosNews/4.0 (+https://github.com/uptobe8/IncendiosNews)",
            "Accept-Language": "es-ES,es;q=0.9",
        },
        timeout=10,
        **kwargs,
    )


def allowed_source(source: str) -> bool:
    s = re.sub(r"[^a-záéíóúüñ0-9 ]+", " ", source.lower()).strip()
    return any(a in s or s in a for a in ALLOWED)


def relevant(title: str, description: str = "") -> bool:
    title = clean(title)
    description = clean(description)
    if not FIRE_RE.search(title + " " + description):
        return False
    if TARGET_RE.search(title):
        return True
    # Generic live pages are allowed only when their description clearly mentions the target area.
    generic = re.search(r"última hora|directo|incendios forestales en españa|emergencia nacional", title, re.I)
    return bool(generic and TARGET_RE.search(description))


def place(title: str, description: str = ""):
    text = f"{title} {description}"
    low = text.lower()
    for province, towns in TOWNS.items():
        for town in towns:
            if town.lower() in low:
                return province, town
    if re.search(r"\bávila\b|\bavila\b", text, re.I):
        return "Ávila", "Provincia de Ávila"
    if re.search(r"\btoledo\b", text, re.I):
        return "Toledo", "Provincia de Toledo"
    if re.search(r"\bmadrid\b|sierra oeste", text, re.I):
        return "Madrid", "Comunidad de Madrid"
    return None, None


def html_date(soup: BeautifulSoup):
    values = []
    for key in ["article:published_time", "article:modified_time", "datePublished", "dateModified"]:
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key}) or soup.find("meta", attrs={"itemprop": key})
        if tag and tag.get("content"):
            values.append(tag["content"])
    for tag in soup.find_all("time"):
        if tag.get("datetime"):
            values.append(tag["datetime"])
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        txt = script.string or script.get_text("", strip=True)
        values.extend(re.findall(r'"(?:datePublished|dateModified)"\s*:\s*"([^"]+)"', txt))
    parsed = [parse_pub(v) for v in values]
    parsed = [v for v in parsed if v]
    return max(parsed, key=lambda x: datetime.fromisoformat(x)) if parsed else None


def row_from_article(url: str, source: str, fallback_title: str = ""):
    r = get(url, allow_redirects=True)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    og = soup.find("meta", property="og:title")
    title = clean(og.get("content") if og else "") or clean(soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else fallback_title)
    desc_tag = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    description = clean(desc_tag.get("content") if desc_tag else "")
    if not relevant(title, description):
        return None
    published = html_date(soup)
    if not published:
        return None
    age = (datetime.now(MADRID_TZ) - datetime.fromisoformat(published)).total_seconds()
    if age > 172800:
        return None
    province, town = place(title, description)
    if not province:
        return None
    return {
        "id": ident(title, source, published),
        "type": "news",
        "severity": "critical" if re.search(r"cortad|evacu|desaloj|confin|cerrad|esalert", title + " " + description, re.I) else "info",
        "province": province,
        "town": town,
        "published": published,
        "source": source,
        "title": title,
        "summary": description[:360] or "Abre la fuente para consultar la actualización completa.",
        "url": url,
    }


def direct_listing(list_url: str, source: str, host_hint: str, limit: int = 18):
    r = get(list_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    candidates, seen = [], set()
    for a in soup.find_all("a", href=True):
        text = clean(a.get_text(" ", strip=True))
        href = urllib.parse.urljoin(list_url, a["href"])
        if host_hint not in urllib.parse.urlparse(href).netloc.lower() or href in seen:
            continue
        if not FIRE_RE.search(text):
            continue
        seen.add(href)
        candidates.append((href, text))
        if len(candidates) >= limit:
            break
    out = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for item in ex.map(lambda pair: row_from_article(pair[0], source, pair[1]), candidates):
            if item:
                out.append(item)
    return out


def direct_media():
    specs = [
        ("https://www.telemadrid.es/ultimas-noticias/", "Telemadrid", "telemadrid.es"),
        ("https://www.europapress.es/madrid/", "Europa Press", "europapress.es"),
        ("https://www.europapress.es/castilla-y-leon/", "Europa Press", "europapress.es"),
        ("https://www.europapress.es/castilla-lamancha/", "Europa Press", "europapress.es"),
    ]
    out, success = [], 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(direct_listing, *spec) for spec in specs]
        for f in futures:
            try:
                out.extend(f.result())
                success += 1
            except Exception:
                pass
    if not success:
        raise RuntimeError("Medios directos no disponibles")
    return out


def google_news():
    def one(query):
        rows = []
        try:
            url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": query, "hl": "es", "gl": "ES", "ceid": "ES:es"})
            r = get(url)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                raw_title = clean(item.findtext("title") or "")
                description = clean(item.findtext("description") or "")
                source_node = item.find("source")
                source = clean(source_node.text if source_node is not None else "") or clean(raw_title.rsplit(" - ", 1)[-1])
                if not raw_title or not allowed_source(source) or not relevant(raw_title, description):
                    continue
                published = parse_pub(item.findtext("pubDate"))
                if not published:
                    continue
                province, town = place(raw_title, description)
                if not province:
                    continue
                title = re.sub(r"\s+-\s+" + re.escape(source) + r"$", "", raw_title, flags=re.I)
                rows.append({
                    "id": ident(title, source, published),
                    "type": "news",
                    "severity": "critical" if re.search(r"cortad|evacu|desaloj|confin|cerrad|esalert", title + " " + description, re.I) else "info",
                    "province": province,
                    "town": town,
                    "published": published,
                    "source": source.rstrip(" ."),
                    "title": title,
                    "summary": "Abre la fuente para consultar el contenido completo y la actualización publicada por el medio.",
                    "url": item.findtext("link") or "",
                })
        except Exception:
            return rows, False
        return rows, True

    out, successes = [], 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for rows, ok in ex.map(one, GOOGLE_QUERIES):
            out.extend(rows)
            successes += int(ok)
    if not successes:
        raise RuntimeError("Google News RSS no disponible")
    return out


def official_items():
    specs = [
        ("https://www.comunidad.madrid/seguridad-emergencias-asem-112/incendio-forestal-sierra-oeste-ifsierraoeste-julio-2026", "Comunidad de Madrid · ASEM 112", "Madrid", "Sierra Oeste", "critical"),
        ("https://www.interior.gob.es/opencms/es/detalle/articulo/Grande-Marlaska-declara-la-emergencia-de-interes-nacional-en-la-Comunidad-de-Madrid-y-en-Avila-por-los-incendios-forestales/", "Ministerio del Interior", "Madrid", "Madrid · Ávila", "critical"),
        ("https://www.interior.gob.es/opencms/eu/detalle/articulo/Interior-amplia-a-la-provincia-de-Toledo-la-declaracion-de-emergencia-de-interes-nacional-por-los-incendios-forestales/", "Ministerio del Interior", "Toledo", "Toledo", "critical"),
    ]
    out = []
    for url, source, province, town, severity in specs:
        try:
            r = get(url, allow_redirects=True)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            og = soup.find("meta", property="og:title")
            title = clean(og.get("content") if og else "") or clean(soup.title.string if soup.title else "")
            published = html_date(soup)
            if not title or not published:
                continue
            desc_tag = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            description = clean(desc_tag.get("content") if desc_tag else "")
            out.append({
                "id": ident(url, published), "type": "official", "severity": severity,
                "province": province, "town": town, "published": published, "source": source,
                "title": title, "summary": description[:400] or "Publicación del organismo oficial.", "url": url,
            })
        except Exception:
            pass
    if not out:
        raise RuntimeError("Fuentes oficiales no disponibles")
    return out


def main():
    seed = json.loads(SEED.read_text("utf-8"))
    fresh, checks = [], {}
    jobs = [("direct_media", direct_media), ("google_news", google_news), ("official", official_items)]
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(fn): name for name, fn in jobs}
        for f in as_completed(futures):
            name = futures[f]
            try:
                part = f.result()
                fresh.extend(part)
                checks[name] = {"ok": True, "items": len(part)}
            except Exception as e:
                checks[name] = {"ok": False, "error": type(e).__name__}

    items = fresh + [x for x in seed.get("items", []) if relevant(x.get("title", ""), x.get("summary", ""))]
    seen, deduped = set(), []
    for x in sorted(items, key=lambda z: z.get("published", ""), reverse=True):
        key = re.sub(r"\W+", " ", x.get("title", "").lower()).strip()[:140]
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(x)

    now = datetime.now(MADRID_TZ).isoformat(timespec="seconds")
    data = {
        "generated_at": now,
        "items": deduped[:220],
        "sources": seed.get("sources", []),
        "checks": checks,
        "refresh_seconds": 300,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    print(f"{len(deduped[:220])} contenidos escritos en {OUT} @ {now}")


if __name__ == "__main__":
    main()
