# FireWatch Centro
Monitor de incendios para Madrid, Ávila y Toledo.

## Incluye
- Next.js dashboard responsive.
- Convex para datos realtime, índices y endpoint HTTP seguro.
- Motor Python para RSS/APIs/páginas permitidas.
- Separación estricta entre alerta oficial y noticia.
- Whitelist de medios y registro de dominios oficiales.
- Deduplicación por externalId/hash.
- Trazabilidad: fuente, dominio, URL, provincia, población, fecha y hora.

## Arranque
1. `npm install`
2. `npx convex dev`
3. Copia `.env.example` a `.env.local` y rellena las variables.
4. `npm run dev`
5. En `ingestion/`: `pip install -r requirements.txt` y `python main.py`.

## Importante
`FIREWATCH_FEEDS` debe contener únicamente feeds/APIs que hayas verificado y autorizado. La whitelist de medios controla qué dominios pueden entrar. Una noticia nunca se etiqueta como alerta oficial.
