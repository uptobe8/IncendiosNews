from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "live_cache.json"
REFRESH_SECONDS = 180
TIMEOUT = 16

OFFICIAL_SOURCES = [
    {"name":"Comunidad de Madrid · ASEM 112","kind":"official","area":"Madrid","url":"https://www.comunidad.madrid/112","desc":"Emergencias, INFOMA, evacuaciones, confinamientos y recomendaciones."},
    {"name":"Junta de Castilla y León · INFOCAL","kind":"official","area":"Ávila","url":"https://analisis.datosabiertos.jcyl.es/explore/dataset/incendios-forestales/map/","desc":"Parte diario oficial en datos abiertos con estado y medios de extinción."},
    {"name":"INFOCAM · Castilla-La Mancha","kind":"official","area":"Toledo","url":"https://infocam.castillalamancha.es/","desc":"Mapa, situación actual, incendios significativos y boletín de riesgo."},
    {"name":"Protección Civil y Emergencias","kind":"official","area":"España","url":"https://www.proteccioncivil.es/","desc":"Red de Alerta Nacional y avisos estatales."},
    {"name":"DGT","kind":"official","area":"Carreteras","url":"https://www.dgt.es/conoce-el-estado-del-trafico/","desc":"Estado y restricciones de tráfico actualizadas."},
    {"name":"AEMET","kind":"official","area":"Meteorología","url":"https://www.aemet.es/","desc":"Avisos meteorológicos y riesgo asociado a condiciones extremas."},
]
MEDIA_SOURCES = [
    {"name":"EFE","kind":"media","area":"General","url":"https://efe.com/","desc":"Agencia de noticias."},
    {"name":"RTVE","kind":"media","area":"General","url":"https://www.rtve.es/noticias/","desc":"Servicio público de información."},
    {"name":"Europa Press","kind":"media","area":"General","url":"https://www.europapress.es/","desc":"Agencia de noticias."},
    {"name":"Cadena SER","kind":"media","area":"General / local","url":"https://cadenaser.com/","desc":"Cobertura nacional y local."},
    {"name":"Onda Cero","kind":"media","area":"General / local","url":"https://www.ondacero.es/","desc":"Cobertura nacional y local."},
    {"name":"COPE","kind":"media","area":"General / local","url":"https://www.cope.es/","desc":"Cobertura nacional y local."},
    {"name":"Telemadrid","kind":"media","area":"Madrid","url":"https://www.telemadrid.es/","desc":"Cobertura autonómica de Madrid."},
    {"name":"Diario de Ávila","kind":"media","area":"Ávila","url":"https://www.diariodeavila.es/","desc":"Cobertura local de Ávila."},
    {"name":"La Tribuna de Toledo","kind":"media","area":"Toledo","url":"https://www.latribunadetoledo.es/","desc":"Cobertura local de Toledo."},
    {"name":"La Vanguardia","kind":"media","area":"General","url":"https://www.lavanguardia.com/","desc":"Cobertura nacional."},
    {"name":"elDiario.es","kind":"media","area":"General","url":"https://www.eldiario.es/","desc":"Cobertura nacional y territorial."},
]
ALLOWED_MEDIA = {x["name"].lower() for x in MEDIA_SOURCES} | {
    "rtve.es", "efe noticias", "europa press", "cadena ser", "onda cero", "cope", "telemadrid",
    "diario de ávila", "la tribuna de toledo", "la vanguardia", "eldiario.es", "el país", "el mundo", "abc"
}

TOWNS = {
    "Madrid":["San Martín de Valdeiglesias","Pelayos de la Presa","Villa del Prado","Valdemaqueda","Navalagamella","Robledo de Chavela","Cadalso de los Vidrios","Chapinería","Colmenar del Arroyo","Fresnedillas de la Oliva","Rozas de Puerto Real","Aldea del Fresno","Navas del Rey","Zarzalejo","Cenicientos","Valdemorillo","El Escorial","Peralejo","Pantano de San Juan","Sierra Oeste"],
    "Ávila":["Burgohondo","Sotillo de la Adrada","Navahondilla","Casillas","Santa María del Tiétar","La Adrada","Piedralaves","Casavieja","Hoyo de Pinares","Villanueva de Ávila","El Tiemblo","Pedro Bernardo","Higuera de las Dueñas","Gavilanes","Mijares","Fresnedilla","Navaluenga","Navalacruz","Hoyocasero","Navalosa","Mombeltrán","Cebreros"],
    "Toledo":["Almorox","La Iglesuela del Tiétar","Sartajada","Almendral de la Cañada","Pelahustán","El Real de San Vicente","Nombela","Escalona","Paredes de Escalona","Hormigos","Méntrida","Santa Cruz del Retamar","Toledo"]
}

def norm(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')

def detect_place(text: str) -> tuple[str,str]:
    n=norm(text)
    for province, towns in TOWNS.items():
        for town in towns:
            if norm(town) in n:
                return province, town
    if "avila" in n: return "Ávila", "Provincia de Ávila"
    if "toledo" in n: return "Toledo", "Provincia de Toledo"
    return "Madrid", "Comunidad de Madrid"

def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def make_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:18]

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)).strip()

def request(url: str, **kwargs: Any) -> requests.Response:
    headers={"User-Agent":"IncendiosCentro/1.0 (+local emergency information aggregator)","Accept-Language":"es-ES,es;q=0.9"}
    r=requests.get(url,headers=headers,timeout=TIMEOUT,**kwargs);r.raise_for_status();return r

def google_news() -> list[dict[str,Any]]:
    queries=[
        'incendio forestal (Madrid OR "Sierra Oeste" OR "Villa del Prado" OR "San Martín de Valdeiglesias") when:2d',
        'incendio (Ávila OR Burgohondo OR Piedralaves OR "Sotillo de la Adrada") when:2d',
        'incendio (Toledo OR Almorox OR "La Iglesuela del Tiétar") when:2d',
    ]
    out=[]
    for q in queries:
        try:
            url="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":q,"hl":"es","gl":"ES","ceid":"ES:es"})
            root=ET.fromstring(request(url).content)
            for it in root.findall(".//item"):
                title=clean(it.findtext("title") or "")
                link=it.findtext("link") or ""
                pub=it.findtext("pubDate") or ""
                source_el=it.find("source")
                source=clean(source_el.text if source_el is not None and source_el.text else title.rsplit(" - ",1)[-1])
                sl=source.lower()
                if not any(a in sl or sl in a for a in ALLOWED_MEDIA):
                    continue
                try:
                    dt=datetime.strptime(pub,"%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc).astimezone()
                    published=dt.isoformat(timespec="seconds")
                except Exception:
                    published=iso_now()
                province,town=detect_place(title)
                out.append({"id":make_id(title,source),"type":"news","severity":"info","province":province,"town":town,"published":published,"source":source,"title":re.sub(r"\s+-\s+"+re.escape(source)+r"$","",title),"summary":"Cobertura localizada por el agregador. Abre la fuente para consultar el contenido completo y la última actualización del medio.","url":link})
        except Exception:
            pass
    return out

def official_madrid() -> list[dict[str,Any]]:
    url="https://www.comunidad.madrid/seguridad-emergencias-asem-112/incendio-forestal-sierra-oeste-ifsierraoeste-julio-2026"
    try:
        text=clean(request(url).text)
        m=re.search(r"Última actualización:\s*([^\.]{5,80})",text,re.I)
        update=m.group(1).strip() if m else "actualización oficial"
        title="Seguimiento oficial del incendio forestal de Sierra Oeste"
        summary="Comunidad de Madrid mantiene en esta página la evolución, municipios afectados, confinamientos, evacuaciones, carreteras y recomendaciones. "+update+"."
        return [{"id":make_id(url,update),"type":"official","severity":"critical","province":"Madrid","town":"Sierra Oeste","published":iso_now(),"source":"Comunidad de Madrid · ASEM 112","title":title,"summary":summary,"url":url}]
    except Exception:return []

def official_jcyl() -> list[dict[str,Any]]:
    url="https://analisis.datosabiertos.jcyl.es/api/explore/v2.1/catalog/datasets/incendios-forestales/records"
    try:
        data=request(url,params={"limit":100,"where":"provincia = 'AVILA'","order_by":"fecha_del_parte desc, hora_del_parte desc"}).json()
        out=[]
        for r in data.get("results",[]):
            town=str(r.get("termino_municipal") or "Provincia de Ávila").title()
            if "SIN INCIDENCIAS" in town.upper(): continue
            date=str(r.get("fecha_del_parte") or "")
            hour=str(r.get("hora_del_parte") or "12:00")[:5]
            try:published=datetime.fromisoformat(f"{date}T{hour}:00+02:00").isoformat()
            except Exception:published=iso_now()
            status=str(r.get("situacion_actual") or "Sin detalle")
            level=str(r.get("nivel") or r.get("nivel_maximo_alcanzado") or "-")
            means=str(r.get("medios_de_extincion") or "")
            surf=str(r.get("tipo_y_has_de_superficie_afectada") or "")
            summary=f"Situación: {status}. IGR/nivel: {level}."+(f" Medios: {means}." if means else "")+(f" Superficie: {surf}." if surf else "")
            out.append({"id":make_id("jcyl",town,date,hour),"type":"official","severity":"critical" if str(level) in {"2","3"} else "alert","province":"Ávila","town":town,"published":published,"source":"Junta de Castilla y León · INFOCAL","title":f"Parte oficial INFOCAL · {town}","summary":summary[:540],"url":"https://analisis.datosabiertos.jcyl.es/explore/dataset/incendios-forestales/map/"})
        return out[:20]
    except Exception:return []

def official_infocam() -> list[dict[str,Any]]:
    url="https://infocam.castillalamancha.es/"
    try:
        text=clean(request(url).text)
        relevant=[]
        for town in TOWNS["Toledo"]:
            if norm(town) in norm(text): relevant.append(town)
        town=relevant[0] if relevant else "Provincia de Toledo"
        return [{"id":make_id("infocam",text[:150]),"type":"official","severity":"alert","province":"Toledo","town":town,"published":iso_now(),"source":"INFOCAM · Castilla-La Mancha","title":"Situación oficial de incendios forestales de Castilla-La Mancha","summary":"INFOCAM publica los últimos incendios significativos, localización, estado, medios movilizados, mapa y boletín de riesgo. Consulta la ficha oficial para el detalle actualizado.","url":url}]
    except Exception:return []

def official_proteccion_civil() -> list[dict[str,Any]]:
    url="https://www.proteccioncivil.es/"
    try:
        soup=BeautifulSoup(request(url).text,"html.parser")
        text=clean(str(soup))
        hits=[]
        for sentence in re.split(r"(?<=[.!?])\s+",text):
            n=norm(sentence)
            if ("incend" in n or "calor" in n or "alerta" in n) and len(sentence)>45:
                hits.append(sentence[:420])
        summary=hits[0] if hits else "Consulta de avisos oficiales y Red de Alerta Nacional de Protección Civil y Emergencias."
        return [{"id":make_id("pc",summary),"type":"official","severity":"alert","province":"Madrid","town":"Madrid / Ávila / Toledo","published":iso_now(),"source":"Protección Civil y Emergencias","title":"Avisos estatales y Red de Alerta Nacional","summary":summary,"url":url}]
    except Exception:return []

def dedupe(items:list[dict[str,Any]]) -> list[dict[str,Any]]:
    seen=set();out=[]
    for x in sorted(items,key=lambda z:z.get("published",""),reverse=True):
        key=norm(re.sub(r"[^\w\s]","",x.get("title","")))[:120]
        if key in seen:continue
        seen.add(key);out.append(x)
    return out

def load_seed() -> dict[str,Any]:
    try:
        return json.loads((ROOT/"seed.json").read_text("utf-8"))
    except Exception:
        return {"generated_at":iso_now(),"items":[],"sources":OFFICIAL_SOURCES+MEDIA_SOURCES}


lock=threading.Lock()
state=load_seed()

def refresh() -> None:
    global state
    seed=load_seed()
    live=[]
    live.extend(official_madrid());live.extend(official_jcyl());live.extend(official_infocam());live.extend(official_proteccion_civil());live.extend(google_news())
    merged=dedupe(live + seed["items"])
    new={"generated_at":iso_now(),"items":merged[:180],"sources":OFFICIAL_SOURCES+MEDIA_SOURCES}
    with lock:
        state=new
        CACHE.write_text(json.dumps(new,ensure_ascii=False,indent=2),"utf-8")

def worker() -> None:
    while True:
        try:refresh()
        except Exception:pass
        time.sleep(REFRESH_SECONDS)

app=FastAPI(title="Incendios Centro Local")
app.mount("/assets",StaticFiles(directory=ROOT/"assets"),name="assets")

@app.on_event("startup")
def startup() -> None:
    if CACHE.exists():
        try:
            global state
            state=json.loads(CACHE.read_text("utf-8"))
        except Exception:pass
    threading.Thread(target=worker,daemon=True).start()

@app.get("/")
def index(): return FileResponse(ROOT/"index.html")

@app.get("/api/feed")
def feed():
    with lock:return state

@app.post("/api/refresh")
def force_refresh():
    threading.Thread(target=refresh,daemon=True).start()
    return {"ok":True,"started":True}

@app.get("/api/status")
def status():
    with lock:return {"ok":True,"generated_at":state.get("generated_at"),"items":len(state.get("items",[]))}

if __name__=="__main__":
    print("\nIncendios Centro — abriendo en http://127.0.0.1:8000\n")
    uvicorn.run(app,host="0.0.0.0",port=8000,log_level="warning")
