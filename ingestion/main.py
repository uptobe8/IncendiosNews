import os, re, json, hashlib, asyncio
from urllib.parse import urlparse
from datetime import datetime, timezone
import httpx, feedparser
from bs4 import BeautifulSoup

PROVINCES=("Madrid","Ávila","Toledo")
OFFICIAL_DOMAINS={"comunidad.madrid","112cmadrid.es","interior.gob.es","proteccioncivil.es","aemet.es","jcyl.es","jccm.es","112.castillalamancha.es","boe.es","defensa.gob.es"}
MEDIA_DOMAINS=set(filter(None,os.getenv("MEDIA_WHITELIST","").split(",")))
FEEDS=list(filter(None,os.getenv("FIREWATCH_FEEDS","").split(",")))
CONVEX_INGEST_URL=os.environ.get("CONVEX_INGEST_URL","")
INGEST_SECRET=os.environ.get("INGEST_SECRET","")

def domain(url:str)->str:
    return urlparse(url).netloc.lower().removeprefix("www.")

def classify_source(url:str):
    d=domain(url)
    if any(d==x or d.endswith('.'+x) for x in OFFICIAL_DOMAINS): return "official"
    if any(d==x or d.endswith('.'+x) for x in MEDIA_DOMAINS): return "media"
    return "rejected"

def province_for(text:str):
    low=text.lower()
    for p in PROVINCES:
        if p.lower() in low: return p
    return None

def clean_html(value:str)->str:
    return BeautifulSoup(value or "","html.parser").get_text(" ",strip=True)

def make_hash(title,url,published):
    raw=f"{title.strip().lower()}|{url}|{published}"
    return hashlib.sha256(raw.encode()).hexdigest()

def normalize(entry,feed_url):
    url=entry.get("link") or feed_url
    verification=classify_source(url)
    if verification=="rejected": return None
    title=clean_html(entry.get("title",""))
    summary=clean_html(entry.get("summary",entry.get("description","")))
    text=f"{title} {summary}"
    if not re.search(r"incend|fuego|forestal|evacua|confin",text,re.I): return None
    province=province_for(text)
    if not province: return None
    dt=entry.get("published_parsed") or entry.get("updated_parsed")
    published=int(datetime(*dt[:6],tzinfo=timezone.utc).timestamp()*1000) if dt else int(datetime.now(timezone.utc).timestamp()*1000)
    h=make_hash(title,url,published)
    return {"externalId":entry.get("id") or h,"kind":"official_alert" if verification=="official" else "news","title":title,"summary":summary[:1800],"url":url,"sourceName":entry.get("source",{}).get("title") or domain(url),"sourceDomain":domain(url),"isOfficial":verification=="official","province":province,"publishedAt":published,"contentHash":h,"verification":"official" if verification=="official" else "whitelisted_media"}

async def push(client,item):
    if not CONVEX_INGEST_URL: return
    r=await client.post(CONVEX_INGEST_URL,json=item,headers={"x-ingest-secret":INGEST_SECRET},timeout=20)
    r.raise_for_status()

async def poll_once():
    async with httpx.AsyncClient(follow_redirects=True,headers={"User-Agent":"FireWatchCentro/1.0"}) as client:
        for feed in FEEDS:
            try:
                resp=await client.get(feed,timeout=20);resp.raise_for_status()
                parsed=feedparser.loads(resp.content)
                for e in parsed.entries:
                    item=normalize(e,feed)
                    if item: await push(client,item)
            except Exception as exc:
                print(json.dumps({"feed":feed,"error":str(exc)},ensure_ascii=False))

async def main():
    interval=max(60,int(os.getenv("POLL_SECONDS","300")))
    while True:
        await poll_once(); await asyncio.sleep(interval)

if __name__=="__main__": asyncio.run(main())
