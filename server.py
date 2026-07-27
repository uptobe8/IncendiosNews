from pathlib import Path
import json, subprocess, sys, threading
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAVE_APSCHEDULER=True
except Exception:
    BackgroundScheduler=None
    CronTrigger=None
    HAVE_APSCHEDULER=False
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from traffic import check_route, refresh_dgt

MADRID_TZ=ZoneInfo('Europe/Madrid')
app=FastAPI(title='IncendiosNews Local V3')
app.mount('/assets',StaticFiles(directory=ROOT/'assets'),name='assets')
app.mount('/data',StaticFiles(directory=ROOT/'data'),name='data')
_scheduler=None
_update_lock=threading.Lock()
_stop_fallback=threading.Event()

def update_feed():
    if not _update_lock.acquire(blocking=False): return
    try:
        subprocess.run([sys.executable,str(ROOT/'scripts'/'update_feed.py')],cwd=ROOT,timeout=50,check=False)
    finally:
        _update_lock.release()

def update_traffic():
    try: refresh_dgt(True)
    except Exception: pass

def _fallback_cron_loop():
    import time
    last_minute=None
    last_five=None
    while not _stop_fallback.is_set():
        now=datetime.now(MADRID_TZ)
        minute_key=now.strftime('%Y%m%d%H%M')
        five_key=now.strftime('%Y%m%d%H')+str(now.minute//5)
        if minute_key!=last_minute:
            last_minute=minute_key
            threading.Thread(target=update_feed,daemon=True).start()
        if five_key!=last_five:
            last_five=five_key
            threading.Thread(target=update_traffic,daemon=True).start()
        time.sleep(1)

@app.on_event('startup')
def startup():
    global _scheduler
    threading.Thread(target=update_feed,daemon=True).start()
    threading.Thread(target=update_traffic,daemon=True).start()
    # Cron real mientras la aplicación local está encendida:
    # noticias cada minuto y DGT cada cinco minutos.
    if HAVE_APSCHEDULER:
        _scheduler=BackgroundScheduler(timezone='Europe/Madrid')
        _scheduler.add_job(update_feed,CronTrigger(second=0),id='news_every_minute',max_instances=1,coalesce=True,replace_existing=True)
        _scheduler.add_job(update_traffic,CronTrigger(minute='*/5',second=10),id='dgt_every_5_minutes',max_instances=1,coalesce=True,replace_existing=True)
        _scheduler.start()
    else:
        threading.Thread(target=_fallback_cron_loop,daemon=True).start()

@app.on_event('shutdown')
def shutdown():
    _stop_fallback.set()
    if _scheduler: _scheduler.shutdown(wait=False)

@app.get('/')
def home(): return FileResponse(ROOT/'index.html')

@app.get('/api/feed')
def feed():
    p=ROOT/'data'/'feed.json'
    if not p.exists(): update_feed()
    return json.loads(p.read_text('utf-8'))

@app.post('/api/refresh')
def refresh():
    threading.Thread(target=update_feed,daemon=True).start()
    return {'ok':True,'started_at':datetime.now(MADRID_TZ).isoformat(timespec='seconds')}

@app.get('/api/traffic')
def traffic(): return refresh_dgt(False)

@app.get('/api/route')
def route(origin:str=Query(min_length=2),destination:str=Query(min_length=2)):
    try: return check_route(origin,destination)
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e))
    except Exception as e: raise HTTPException(status_code=503,detail='No se ha podido verificar la ruta en este momento')

@app.get('/api/health')
def health():
    feed_path=ROOT/'data'/'feed.json'
    generated_at=None
    checks={}
    try:
        payload=json.loads(feed_path.read_text('utf-8'))
        generated_at=payload.get('generated_at')
        checks=payload.get('checks',{})
    except Exception:
        pass
    return {
        'ok':True,
        'news_cron':'cada 60 segundos',
        'dgt_cron':'cada 5 minutos',
        'browser_refresh':'cada 20 segundos',
        'scheduler':'APScheduler' if HAVE_APSCHEDULER else 'bucle local de respaldo',
        'generated_at':generated_at,
        'checks':checks,
        'time':datetime.now(MADRID_TZ).isoformat(timespec='seconds')
    }

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='0.0.0.0',port=8765,log_level='warning')
