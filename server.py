from pathlib import Path
import subprocess,sys,threading,time,json
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
ROOT=Path(__file__).resolve().parent
app=FastAPI(title='IncendiosNews Local')
app.mount('/assets',StaticFiles(directory=ROOT/'assets'),name='assets'); app.mount('/data',StaticFiles(directory=ROOT/'data'),name='data')
def update():
    try: subprocess.run([sys.executable,str(ROOT/'scripts'/'update_feed.py')],cwd=ROOT,timeout=70,check=False)
    except Exception: pass
def loop():
    while True:update();time.sleep(300)
@app.on_event('startup')
def start(): threading.Thread(target=loop,daemon=True).start()
@app.get('/')
def home(): return FileResponse(ROOT/'index.html')
@app.get('/api/feed')
def feed():
    p=ROOT/'data'/'feed.json';return json.loads(p.read_text('utf-8'))
@app.post('/api/refresh')
def refresh(): threading.Thread(target=update,daemon=True).start();return {'ok':True}
if __name__=='__main__':
    import uvicorn;uvicorn.run(app,host='0.0.0.0',port=8000,log_level='warning')
