# IncendiosNews V3

## Actualización real
Al abrir la aplicación con `start.command` (Mac) o `start.bat` (Windows), se inicia un backend local y un cron real:

- Noticias y páginas verificadas: cada 60 segundos.
- La interfaz vuelve a leer el feed cada 20 segundos, sin recargar la página.
- Incidencias de tráfico DGT: cada 5 minutos. La propia DGT declara para SRTI DATEX II una frecuencia de actualización de hasta 5 minutos.

El archivo `IncendiosNews_V3_ABRIR_DIRECTO.html` sirve para comprobar el diseño sin instalar nada, pero al abrirse como archivo no puede ejecutar el cron ni el comprobador DGT. La propia interfaz lo indica para no confundir una instantánea con datos en tiempo real.

## Fuentes
La actualización combina:
- Telemadrid y Europa Press mediante lectura directa de sus páginas de actualidad.
- Google News RSS y Bing News RSS, filtrados a medios configurados como verificados.
- Fuentes oficiales con fecha verificable, como Departamento de Seguridad Nacional y ASEM 112.
- Accesos directos a INFOCAL, INFOCAM, Protección Civil, AEMET y DGT.

Si una fuente no responde, el estado de la aplicación no la presenta como conectada.

## Rutas y cortes
La sección `¿Puedo llegar?` utiliza:
- Nominatim / OpenStreetMap para localizar origen y destino.
- OSRM para calcular el recorrido.
- DGT SRTI DATEX II para incidencias oficiales de tráfico.

Se comparan las carreteras y la proximidad geográfica de las incidencias con el recorrido calculado. Un resultado verde significa únicamente que no consta un corte DGT en el recorrido comprobado; no garantiza el acceso si existe un control local, una evacuación o una orden de emergencia posterior.

## Uso en móvil y tablet
El servidor escucha en `0.0.0.0:8765`. Al arrancar muestra también la dirección de red local del ordenador. Un móvil o tablet conectado a la misma Wi‑Fi puede abrir esa dirección en el navegador mientras el ordenador mantenga el servidor encendido.
