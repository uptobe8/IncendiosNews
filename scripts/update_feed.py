from __future__ import annotations
import hashlib, json, re, urllib.parse, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / 'seed.json'
OUT = ROOT / 'data' / 'feed.json'
MADRID_TZ=ZoneInfo('Europe/Madrid')

ALLOWED = {
    'efe','rtve','europa press','cadena ser','onda cero','telemadrid','diario de ávila',
    'la tribuna de toledo','el país','abc','la vanguardia','el español','madrid actual',
    '20minutos','el mundo','la razón','castilla-la mancha media','tribuna de ávila'
}
OFFICIAL_NAMES = {
    'departamento de seguridad nacional','comunidad de madrid','asem 112','112 comunidad de madrid',
    'junta de castilla y león','infocal','infocam','castilla-la mancha','protección civil','dgt','aemet'
}
TOWNS = {
    'Madrid':['San Martín de Valdeiglesias','Villa del Prado','Pelayos de la Presa','Chapinería','Navas del Rey','Cenicientos','Aldea del Fresno','Sierra Oeste','Valdemaqueda','Robledo de Chavela','Zarzalejo','Navalagamella','Colmenar del Arroyo','Fresnedillas de la Oliva'],
    'Ávila':['Burgohondo','Sotillo de la Adrada','Piedralaves','La Adrada','Casavieja','Mijares','Navaluenga','El Tiemblo','Higuera de las Dueñas','Gavilanes','Fresnedilla','Navahondilla','Hoyo de Pinares'],
    'Toledo':['Almorox','La Iglesuela del Tiétar','Méntrida','Escalona','El Real de San Vicente','Castillo de Bayuela','San Román de los Montes','Almendral de la Cañada']
}
GOOGLE_QUERIES = [
    'incendio Madrid Ávila Toledo when:1d',
    'incendio Sierra Oeste Madrid when:1d',
    'incendio Burgohondo Ávila when:1d',
    'incendio Almorox Toledo when:1d',
    'carreteras cortadas incendio Madrid Ávila Toledo when:1d',
    'evacuación incendio Madrid Ávila Toledo when:1d',
    'confinamiento incendio Madrid Ávila Toledo when:1d',
    'M-501 M-507 M-512 M-533 incendio when:1d',
    'N-403 incendio Ávila Toledo when:1d',
]

def clean(x: str | None) -> str:
    return re.sub(r'\s+', ' ', BeautifulSoup(x or '', 'html.parser').get_text(' ', strip=True)).strip()

def ident(*parts: str) -> str:
    return hashlib.sha1('|'.join(parts).encode('utf-8')).hexdigest()[:18]

def place(text: str):
    low = text.lower()
    matches=[]
    for province, towns in TOWNS.items():
        for town in towns:
            if town.lower() in low:
                matches.append((province,town))
    if matches:
        return matches[0]
    if 'ávila' in low or 'avila' in low: return 'Ávila','Provincia de Ávila'
    if 'toledo' in low: return 'Toledo','Provincia de Toledo'
    if 'madrid' in low: return 'Madrid','Comunidad de Madrid'
    return 'Madrid','Madrid · Ávila · Toledo'

def get(url: str, **kwargs):
    return requests.get(url, headers={
        'User-Agent':'IncendiosNews/3.0 (+informacion de emergencia; agregador local)',
        'Accept-Language':'es-ES,es;q=0.9'
    }, timeout=4, **kwargs)

def parse_pub(value: str | None):
    if not value: return None
    try:
        d=parsedate_to_datetime(value)
        if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(MADRID_TZ).isoformat(timespec='seconds')
    except Exception:
        pass
    try:
        return datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(MADRID_TZ).isoformat(timespec='seconds')
    except Exception:
        return None

def allowed_source(src: str) -> bool:
    s=src.lower().strip()
    return any(a in s or s in a for a in ALLOWED)

def google_news():
    def one(query):
        rows=[]
        try:
            u='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query,'hl':'es','gl':'ES','ceid':'ES:es'})
            r=get(u); r.raise_for_status(); root=ET.fromstring(r.content)
            for it in root.findall('.//item'):
                title=clean(it.findtext('title') or '')
                source_node=it.find('source')
                src=clean(source_node.text if source_node is not None else '') or clean(title.rsplit(' - ',1)[-1])
                if not title or not allowed_source(src): continue
                published=parse_pub(it.findtext('pubDate'))
                if not published: continue
                province,town=place(title)
                rows.append({
                    'id':ident(title,src),'type':'news','severity':'critical' if re.search(r'cortad|evacu|desaloj|confin|cerrad',title,re.I) else 'info',
                    'province':province,'town':town,'published':published,'source':src,
                    'title':re.sub(r'\s+-\s+'+re.escape(src)+r'$', '', title, flags=re.I),
                    'summary':'Abre la fuente para consultar el contenido completo y la actualización publicada por el medio.',
                    'url':it.findtext('link') or ''
                })
        except Exception:
            return rows,False
        return rows,True
    out=[]; successes=0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for rows,ok in ex.map(one,GOOGLE_QUERIES):
            out.extend(rows); successes += int(ok)
    if not successes: raise RuntimeError('Google News RSS no disponible')
    return out

def bing_news():
    queries=['incendio Madrid Ávila Toledo','incendio Sierra Oeste Madrid','incendio Burgohondo Ávila','incendio Almorox Toledo','carreteras cortadas incendios Madrid Ávila Toledo']
    def one(query):
        rows=[]
        try:
            u='https://www.bing.com/news/search?'+urllib.parse.urlencode({'q':query,'format':'rss','setlang':'es-es'})
            r=get(u); r.raise_for_status(); root=ET.fromstring(r.content)
            for it in root.findall('.//item'):
                title=clean(it.findtext('title') or ''); desc=clean(it.findtext('description') or ''); link=it.findtext('link') or ''; src=''
                hay=(title+' '+desc+' '+link).lower()
                for a in ALLOWED:
                    if a in hay: src=a.title(); break
                if not src or not title: continue
                published=parse_pub(it.findtext('pubDate'))
                if not published: continue
                province,town=place(title+' '+desc)
                rows.append({'id':ident(title,link),'type':'news','severity':'critical' if re.search(r'cortad|evacu|desaloj|confin|cerrad',title+' '+desc,re.I) else 'info','province':province,'town':town,'published':published,'source':src,'title':title,'summary':desc[:360] or 'Abre la fuente para consultar el contenido completo.','url':link})
        except Exception:
            return rows,False
        return rows,True
    out=[]; successes=0
    with ThreadPoolExecutor(max_workers=5) as ex:
        for rows,ok in ex.map(one,queries):
            out.extend(rows); successes += int(ok)
    if not successes: raise RuntimeError('Bing News RSS no disponible')
    return out

def html_date(soup: BeautifulSoup):
    candidates=[]
    for key in ['article:published_time','article:modified_time','datePublished','dateModified']:
        tag=soup.find('meta',attrs={'property':key}) or soup.find('meta',attrs={'name':key}) or soup.find('meta',attrs={'itemprop':key})
        if tag and tag.get('content'): candidates.append(tag['content'])
    for t in soup.find_all('time'):
        if t.get('datetime'): candidates.append(t['datetime'])
    # JSON-LD
    for sc in soup.find_all('script',attrs={'type':'application/ld+json'}):
        txt=sc.string or sc.get_text('',strip=True)
        for m in re.findall(r'"(?:datePublished|dateModified)"\s*:\s*"([^"]+)"',txt): candidates.append(m)
    vals=[parse_pub(x) for x in candidates]
    vals=[v for v in vals if v]
    return max(vals,key=lambda x:datetime.fromisoformat(x)) if vals else None

def scrape_official(url: str, source: str, province: str, town: str, severity='alert'):
    try:
        r=get(url,allow_redirects=True); r.raise_for_status()
        soup=BeautifulSoup(r.text,'html.parser')
        title=clean((soup.find('meta',property='og:title') or {}).get('content') if soup.find('meta',property='og:title') else '') or clean(soup.title.string if soup.title else '')
        published=html_date(soup)
        if not published or not title: return None
        desc_tag=soup.find('meta',property='og:description') or soup.find('meta',attrs={'name':'description'})
        summary=clean(desc_tag.get('content') if desc_tag else '')[:400]
        return {'id':ident(url,published),'type':'official','severity':severity,'province':province,'town':town,'published':published,'source':source,'title':title,'summary':summary or 'Publicación del organismo oficial.','url':url}
    except Exception:
        return None


FRESH_KEYWORDS = re.compile(r'incendi|fuego|evacu|desaloj|confin|carretera|corte|dgt|esalert|sierra oeste|burgohondo|almorox|valdemaqueda|quemad|humo|ume|san martín de valdeiglesias|villa del prado|pelayos de la presa', re.I)

def direct_listing(list_url: str, source: str, host_hint: str, limit: int = 8):
    try:
        r=get(list_url); r.raise_for_status(); soup=BeautifulSoup(r.text,'html.parser')
    except Exception as e:
        raise RuntimeError(f'Listado no disponible: {source}') from e
    candidates=[]; seen=set()
    for a in soup.find_all('a',href=True):
        text=clean(a.get_text(' ',strip=True)); href=urllib.parse.urljoin(list_url,a['href'])
        if host_hint not in urllib.parse.urlparse(href).netloc.lower(): continue
        if not FRESH_KEYWORDS.search(text): continue
        if href in seen: continue
        seen.add(href); candidates.append((href,text))
        if len(candidates)>=limit: break
    def one(pair):
        href,fallback_title=pair
        try:
            rr=get(href); rr.raise_for_status(); ss=BeautifulSoup(rr.text,'html.parser')
            og=ss.find('meta',property='og:title')
            title=clean(og.get('content') if og else '') or clean(ss.find('h1').get_text(' ',strip=True) if ss.find('h1') else fallback_title)
            if not title or not FRESH_KEYWORDS.search(title): return None
            published=html_date(ss)
            if not published: return None
            age=(datetime.now(MADRID_TZ)-datetime.fromisoformat(published)).total_seconds()
            if age > 172800: return None
            desc_tag=ss.find('meta',property='og:description') or ss.find('meta',attrs={'name':'description'})
            desc=clean(desc_tag.get('content') if desc_tag else '')
            province,town=place(title+' '+desc)
            return {'id':ident(title,source,published),'type':'news','severity':'critical' if re.search(r'cortad|evacu|desaloj|confin|cerrad|esalert',title+' '+desc,re.I) else 'info','province':province,'town':town,'published':published,'source':source,'title':title,'summary':desc[:360] or 'Abre la fuente para consultar la actualización completa.','url':href}
        except Exception:
            return None
    out=[]
    with ThreadPoolExecutor(max_workers=6) as ex:
        for row in ex.map(one,candidates):
            if row: out.append(row)
    return out

def direct_media():
    specs=[('https://www.telemadrid.es/ultimas-noticias/','Telemadrid','telemadrid.es',8),('https://www.europapress.es/sociedad/','Europa Press','europapress.es',8)]
    out=[]; successes=0
    with ThreadPoolExecutor(max_workers=2) as ex:
        futures=[ex.submit(direct_listing,*sp) for sp in specs]
        for f in futures:
            try:
                out.extend(f.result()); successes += 1
            except Exception:
                pass
    if not successes: raise RuntimeError('Medios directos no disponibles')
    return out

def official_items():
    out=[]
    now=datetime.now(MADRID_TZ)
    mon=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'][now.month-1]
    daily=f'https://www.dsn.gob.es/es/actualidad/Ultima-hora/nacional-iiff-{now.day:02d}{mon}{now.year}'
    specs=[
        (daily,'Departamento de Seguridad Nacional','Madrid','Madrid · Ávila · Toledo','critical'),
        ('https://www.comunidad.madrid/seguridad-emergencias-asem-112/incendio-forestal-sierra-oeste-ifsierraoeste-julio-2026','Comunidad de Madrid · ASEM 112','Madrid','Sierra Oeste','critical'),
    ]
    with ThreadPoolExecutor(max_workers=len(specs)) as ex:
        futures=[ex.submit(scrape_official,*spec) for spec in specs]
        for f in futures:
            try:
                item=f.result()
                if item: out.append(item)
            except Exception:
                pass
    if not out: raise RuntimeError('Fuentes oficiales no disponibles')
    return out

def main():
    seed=json.loads(SEED.read_text('utf-8'))
    fresh=[]
    checks={}
    jobs=[('direct_media',direct_media),('google_news',google_news),('bing_news',bing_news),('official',official_items)]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures={ex.submit(fn):name for name,fn in jobs}
        for f in as_completed(futures):
            name=futures[f]
            try:
                part=f.result(); fresh.extend(part); checks[name]={'ok':True,'items':len(part)}
            except Exception as e:
                checks[name]={'ok':False,'error':type(e).__name__}
    items=fresh+seed.get('items',[])
    seen=set(); ded=[]
    for x in sorted(items,key=lambda z:z.get('published',''),reverse=True):
        key=re.sub(r'\W+',' ',x.get('title','').lower()).strip()[:130]
        if not key or key in seen: continue
        seen.add(key); ded.append(x)
    now=datetime.now(MADRID_TZ).isoformat(timespec='seconds')
    data={'generated_at':now,'items':ded[:220],'sources':seed.get('sources',[]),'checks':checks,'refresh_seconds':60}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
    print(f'{len(ded[:220])} contenidos escritos en {OUT} @ {now}')

if __name__=='__main__':
    main()
