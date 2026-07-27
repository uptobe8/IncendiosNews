from __future__ import annotations
import json, math, re, threading, time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from rdflib import Graph, RDF, URIRef, BNode, Literal

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'data'/'traffic_cache.json'
DGT_URL='https://infocar.dgt.es/datex2/lod/dgt/incidencias.rdf'
_lock=threading.Lock()

def _get(url, **kw):
    return requests.get(url,headers={'User-Agent':'IncendiosNews/3.0','Accept-Language':'es-ES,es;q=0.9'},timeout=25,**kw)

def _local(uri):
    s=str(uri); return re.split(r'[#/]',s)[-1]

def _norm(s):
    return re.sub(r'[^A-Z0-9]+','',str(s).upper())

def _road_tokens(text):
    return set(re.findall(r'\b(?:AP|A|M|N|CM|CL|AV|TO|EX|SA|SG|VA|LE|BU)[-\s]?\d{1,4}\b',str(text).upper()))

def _collect(g:Graph, node, depth=4, seen=None):
    if seen is None: seen=set()
    if depth<0 or node in seen: return []
    seen.add(node); out=[]
    for p,o in g.predicate_objects(node):
        k=_local(p)
        if isinstance(o,Literal): out.append((k,str(o)))
        elif isinstance(o,(URIRef,BNode)):
            out.append((k,_local(o)))
            out.extend(_collect(g,o,depth-1,seen))
    return out

def parse_dgt(data:bytes):
    g=Graph(); g.parse(data=data,format='xml')
    candidates=set()
    keywords=('SituationRecord','Accident','AbnormalTraffic','Obstruction','RoadOrCarriagewayOrLaneManagement','WeatherRelatedRoadConditions','VehicleObstruction','PoorEnvironmentConditions')
    for s,o in g.subject_objects(RDF.type):
        if any(k.lower() in str(o).lower() for k in keywords): candidates.add(s)
    # Fallback: subjects that directly expose coordinates.
    if not candidates:
        for s,p,o in g:
            if 'latitude' in _local(p).lower(): candidates.add(s)
    incidents=[]; seen_sig=set()
    for s in candidates:
        vals=_collect(g,s,5,set())
        by={}
        for k,v in vals: by.setdefault(k.lower(),[]).append(v)
        def first_containing(parts):
            for k,vs in by.items():
                if any(p in k for p in parts):
                    for v in vs:
                        if v not in ('','None'): return v
            return None
        lat=first_containing(['latitude']); lon=first_containing(['longitude'])
        try: lat=float(str(lat).replace(',','.')) if lat is not None else None
        except: lat=None
        try: lon=float(str(lon).replace(',','.')) if lon is not None else None
        except: lon=None
        road=first_containing(['roadnumber','roadname','affectedroad','roadidentifier','locationdescriptor'])
        comment=[]
        for k,vs in by.items():
            if any(x in k for x in ('comment','value','description','type','cause','severity','traffic','management','obstruction')):
                for v in vs:
                    if len(v)>2 and v not in comment: comment.append(v)
        description=' · '.join(comment[:8])[:700]
        if not road and not description and lat is None: continue
        sig=(round(lat,4) if lat is not None else None,round(lon,4) if lon is not None else None,road,description[:120])
        if sig in seen_sig: continue
        seen_sig.add(sig)
        incidents.append({'road':road or '', 'description':description or 'Incidencia de tráfico DGT', 'lat':lat,'lon':lon,'road_tokens':sorted(_road_tokens((road or '')+' '+description))})
    return incidents

def refresh_dgt(force=False):
    with _lock:
        if not force and CACHE.exists():
            try:
                cached=json.loads(CACHE.read_text('utf-8'))
                age=time.time()-datetime.fromisoformat(cached['checked_at']).timestamp()
                if age < 280: return cached
            except Exception: pass
        try:
            r=_get(DGT_URL); r.raise_for_status(); incidents=parse_dgt(r.content)
            payload={'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),'ok':True,'incidents':incidents,'source':DGT_URL}
            CACHE.write_text(json.dumps(payload,ensure_ascii=False),'utf-8')
            return payload
        except Exception as e:
            if CACHE.exists():
                try:
                    cached=json.loads(CACHE.read_text('utf-8')); cached['ok']=False; cached['stale']=True; cached['error']=type(e).__name__; return cached
                except Exception: pass
            return {'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),'ok':False,'incidents':[],'source':DGT_URL,'error':type(e).__name__}

def geocode(q:str):
    r=_get('https://nominatim.openstreetmap.org/search',params={'q':q,'format':'jsonv2','limit':1,'countrycodes':'es'}); r.raise_for_status(); arr=r.json()
    if not arr: raise ValueError(f'No se encuentra: {q}')
    return {'lat':float(arr[0]['lat']),'lon':float(arr[0]['lon']),'display_name':arr[0].get('display_name',q)}

def osrm_route(a,b):
    u=f"https://router.project-osrm.org/route/v1/driving/{a['lon']},{a['lat']};{b['lon']},{b['lat']}"
    r=_get(u,params={'overview':'full','geometries':'geojson','steps':'true','alternatives':'false'}); r.raise_for_status(); data=r.json()
    if data.get('code')!='Ok' or not data.get('routes'): raise ValueError('No se ha podido calcular la ruta')
    route=data['routes'][0]
    names=[]
    for leg in route.get('legs',[]):
        for st in leg.get('steps',[]):
            if st.get('name'): names.append(st['name'])
            if st.get('ref'): names.append(st['ref'])
    return {'geometry':route['geometry']['coordinates'],'distance_m':route['distance'],'duration_s':route['duration'],'road_text':' '.join(names)}

def hav(a,b):
    lat1,lon1=a; lat2,lon2=b; R=6371.0
    p1,p2=math.radians(lat1),math.radians(lat2); dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    x=math.sin(dlat/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(x))

def min_distance_to_route(lat,lon,geometry):
    if lat is None or lon is None or not geometry: return None
    step=max(1,len(geometry)//180)
    return min(hav((lat,lon),(pt[1],pt[0])) for pt in geometry[::step])

def check_route(origin:str,destination:str):
    a=geocode(origin); b=geocode(destination); route=osrm_route(a,b); traffic=refresh_dgt(False)
    rtokens=_road_tokens(route['road_text'])
    relevant=[]
    blocking_words=('closed','closure','blocked','road closed','cortad','cerrad','interrump','restric','no traffic','impassable')
    for inc in traffic.get('incidents',[]):
        d=min_distance_to_route(inc.get('lat'),inc.get('lon'),route['geometry'])
        itokens=set(inc.get('road_tokens') or [])
        road_match=bool(rtokens & itokens)
        near=d is not None and d<=5.0
        if not (road_match or near): continue
        text=((inc.get('road') or '')+' '+(inc.get('description') or '')).lower()
        blocking=any(w in text for w in blocking_words)
        row=dict(inc); row['distance_km']=0.0 if road_match and d is None else d; row['blocking']=blocking; relevant.append(row)
    relevant.sort(key=lambda x:(not x.get('blocking'), x.get('distance_km') if x.get('distance_km') is not None else 999))
    if not traffic.get('incidents') and not traffic.get('ok'):
        state='unknown'; title='DGT no disponible en este momento'; message='La ruta se ha calculado, pero no se ha podido contrastar el servicio oficial de incidencias. Revisa el mapa DGT o llama al 011 antes de salir.'
    elif any(x.get('blocking') and (x.get('distance_km') is None or x.get('distance_km')<=3.0) for x in relevant):
        state='blocked'; title='Constan incidencias compatibles con un corte en el recorrido'; message='No inicies el trayecto sin revisar las incidencias detalladas y la señalización oficial. La situación puede cambiar rápidamente.'
    elif relevant:
        state='caution'; title='Hay incidencias DGT próximas al recorrido'; message='El trayecto requiere precaución. Revisa cada incidencia y vuelve a comprobar antes de salir.'
    else:
        state='clear'; title='No consta un corte DGT en el recorrido comprobado'; message='Esto no garantiza el acceso: pueden existir cortes locales, controles de emergencia o cambios posteriores a la última actualización.'
    return {'state':state,'title':title,'message':message,'origin':a,'destination':b,'geometry':route['geometry'],'distance_km':round(route['distance_m']/1000,1),'duration_min':round(route['duration_s']/60),'incidents':relevant[:20],'traffic_checked_at':traffic.get('checked_at'),'traffic_ok':traffic.get('ok',False)}
