# C106 — Resultados: oro y plata del viernes en 2003-2009 (Dukascopy, precio medio bid/ask) — 05-nov-2026
Preregistro commit be9b0fc (antes de tener los datos). Script `c106_metales_viernes_2003_2009.py`, salida `c106_resultados.txt`.
Datos: Dukascopy XAUUSD/XAGUSD 5 min bid y ask, 2003-05 → 2009-12, descargados por el usuario.

| | n | Media | t | Años + | Veredicto |
|---|---|---|---|---|---|
| **Oro viernes 16:00-16:55** | 298 | **−0,13 pb** | −0,24 | 2/7 | **NO CONFIRMADA** |
| Plata viernes 16:30-16:55 | 237 | −3,87 pb | −1,77 | 2/7 | NO CONFIRMADA (datos no fiables, ver abajo) |
Oro por año: 2003 −2,1 · 2004 −0,8 · 2005 −0,7 · 2006 −2,5 · 2007 +2,2 · 2008 −1,4 · 2009 +2,8. Placebo lunes-jueves: todos |t| < 1,4.

Calidad de los datos:
- Oro: buena. En 2009 los viernes coinciden con HistData (correlación 0,97; medias +3,5 y +3,9 pb). Spread medio 5-11 pb.
- Plata: mala. Spread medio el viernes 16-17 h de 74-347 pb y muchas velas vacías antes de 2006: el precio medio no es fiable.
  La prueba de la plata queda sin valor (ni a favor ni en contra).

Lectura: en 2003-2008 el efecto del oro del viernes NO existía; aparece desde 2009 (y en 2010-2026 es fuerte en dos fuentes: contado
y futuro GC). El efecto parece nacer con la estructura de mercado actual (negociación electrónica 23 h en Globex desde 2006-2008,
ETF de oro, coberturas al cierre semanal), no es una regularidad intemporal. No invalida 2010-2026, pero indica que puede depender
del régimen de mercado y desaparecer si este cambia. Contador +2.
