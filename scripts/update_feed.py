from __future__ import annotations
import hashlib,json,re,urllib.parse,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
SEED=ROOT/'seed.json'; OUT=ROOT/'data'/'feed.json'
ALLOWED=['efe','rtve','europa press','cadena ser','onda cero','telemadrid','diario de ávila','la tribuna de toledo','el país','abc','la vanguardia']
TOWNS={'Madrid':['San Martín de Valdeiglesias','Villa del Prado','Pelayos de la Presa','Chapinería','Navas del Rey','Cenicientos','Aldea del Fresno','Sierra Oeste'],'Ávila':['Burgohondo','Sotillo de la Adrada','Piedralaves','La Adrada','Casavieja','Mijares','Navaluenga','El Tiemblo'],'Toledo':['Almorox','La Iglesuela del Tiétar','Méntrida','Escalona','Toledo']}
def clean(x): return re.sub(r'\s+',' ',BeautifulSoup(x or '','html.parser').get_text(' ',strip=True)).strip()
def ident(*p): return hashlib.sha1('|'.join(p).encode()).hexdigest()[:18]
def place(t):
    low=t.lower()
    for p,ts in TOWNS.items():
        for town in ts:
            if town.lower() in low:return p,town
    if 'ávila' in low:return 'Ávila','Provincia de Ávila'
    if 'toledo' in low:return 'Toledo','Provincia de Toledo'
    return 'Madrid','Comunidad de Madrid'
def get(url,**kw):
    return requests.get(url,headers={'User-Agent':'IncendiosNews/2.0','Accept-Language':'es-ES'},timeout=18,**kw)
def news():
    out=[]
    for q in ['incendio Madrid Ávila Toledo when:2d','incendio Sierra Oeste Madrid when:2d','incendio Burgohondo Ávila when:2d','incendio Almorox Toledo when:2d']:
        try:
            u='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q,'hl':'es','gl':'ES','ceid':'ES:es'})
            root=ET.fromstring(get(u).content)
            for it in root.findall('.//item'):
                title=clean(it.findtext('title') or ''); src=clean((it.find('source').text if it.find('source') is not None else '') or title.rsplit(' - ',1)[-1]); sl=src.lower()
                if not any(a in sl or sl in a for a in ALLOWED):continue
                pub=it.findtext('pubDate') or ''
                try:published=datetime.strptime(pub,'%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=timezone.utc).astimezone().isoformat(timespec='seconds')
                except:published=datetime.now().astimezone().isoformat(timespec='seconds')
                p,t=place(title); out.append({'id':ident(title,src),'type':'news','severity':'info','province':p,'town':t,'published':published,'source':src,'title':re.sub(r'\s+-\s+'+re.escape(src)+r'$','',title),'summary':'Abre la fuente para consultar el contenido completo y su última actualización.','url':it.findtext('link') or ''})
        except Exception: pass
    return out
def official():
    now=datetime.now().astimezone().isoformat(timespec='seconds')
    return [
      {'id':'live-mad','type':'official','severity':'critical','province':'Madrid','town':'Sierra Oeste','published':now,'source':'Comunidad de Madrid · ASEM 112','title':'Seguimiento oficial del incendio forestal de Sierra Oeste','summary':'Página oficial de ASEM 112 con evolución, municipios afectados, evacuaciones, confinamientos y recomendaciones.','url':'https://www.comunidad.madrid/seguridad-emergencias-asem-112/incendio-forestal-sierra-oeste-ifsierraoeste-julio-2026'},
      {'id':'live-infocam','type':'official','severity':'alert','province':'Toledo','town':'Provincia de Toledo','published':now,'source':'INFOCAM · Castilla-La Mancha','title':'Mapa y situación oficial de incendios forestales de Castilla-La Mancha','summary':'INFOCAM publica mapa, últimos incendios significativos y boletín oficial de riesgo.','url':'https://infocam.castillalamancha.es/'},
      {'id':'live-infocal','type':'official','severity':'alert','province':'Ávila','town':'Provincia de Ávila','published':now,'source':'Junta de Castilla y León · INFOCAL','title':'Partes oficiales de incendios forestales de Castilla y León','summary':'Fuente oficial de datos abiertos de incendios forestales, actualizada dos veces al día.','url':'https://analisis.datosabiertos.jcyl.es/explore/dataset/incendios-forestales/information/'}]
def main():
    seed=json.loads(SEED.read_text('utf-8')); items=official()+news()+seed.get('items',[]); seen=set(); ded=[]
    for x in sorted(items,key=lambda z:z.get('published',''),reverse=True):
        k=re.sub(r'\W+',' ',x.get('title','').lower())[:100]
        if k in seen:continue
        seen.add(k);ded.append(x)
    data={'generated_at':datetime.now().astimezone().isoformat(timespec='seconds'),'items':ded[:160],'sources':seed.get('sources',[])}
    OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
    print(f'{len(ded[:160])} contenidos escritos en {OUT}')
if __name__=='__main__':main()
