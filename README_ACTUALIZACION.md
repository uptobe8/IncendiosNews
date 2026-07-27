# IncendiosNews · versión visual

- `index.html`: versión para GitHub Pages.
- `IncendiosNews_ABRIR_DIRECTO.html`: se abre directamente desde Archivos/Finder y mantiene una instantánea verificada si no puede conectarse.
- `data/feed.json`: datos que consume la web estática.
- `.github/workflows/update-feed.yml`: actualiza el feed cada 10 minutos en GitHub Pages.
- `server.py`: modo local con actualización cada 5 minutos.

Para servidor local: `python -m pip install -r requirements.txt` y `python server.py`.
