# PREREGISTRO C76 — Continuación 5 minutos después de noticias (FOMC, rueda de prensa, empleo) en oro y EURUSD — 27-oct-2026

Redactado y subido a git ANTES de calcular. Idea propuesta por el usuario (vía ChatGPT): tras una noticia de alto impacto,
el precio sigue moviéndose en la dirección de la reacción inicial durante varios minutos (respuesta lenta a la sorpresa).
Se entra 5 minutos después de la publicación (fuera de la ventana de ±2 min que prohíbe FTMO). Pruebas previas de la familia
(deriva previa al FOMC, NFP, IPC, reversión tras noticias: C15, C16, C30, C33) fueron negativas; esta variante (continuación
condicionada a la dirección inicial) no se había probado.

## Eventos (hora de Nueva York)
- **FOMC, comunicado 14:00**: reuniones programadas (`n/fomc.csv`, de federalreserve.gov) desde 2013-03 (antes la hora
  variaba entre 12:30 y 14:15) hasta 2026-09.
- **FOMC, rueda de prensa 14:30**: reuniones programadas desde 2019 (desde entonces hay rueda de prensa en todas).
- **Empleo (NFP) 08:30**: no hay calendario descargable (bls.gov bloquea). Para cada mes 2010-07 → 2026-09, candidatos =
  1.er y 2.º viernes del mes y el jueves anterior a un viernes festivo; se elige el que tenga mayor |rentabilidad| del ES (S&P,
  otro mercado, Databento) de 08:29 a 08:31. Se usa el ES para no seleccionar con la serie que se evalúa.

## Regla (igual para los tres eventos; T = hora del evento)
Señal = signo de P(T+5 min) − P(T), con P(T) = cierre del último minuto antes de T. Posición en esa dirección de T+5 a T+30
(precio = cierre del último minuto anterior a cada hora, buscando hasta 10 minutos atrás). Si la señal es 0 o falta un precio,
no hay operación.

## Mercados y costes (ida y vuelta, el DOBLE del coste normal por ser hora de noticia)
- Oro: futuro GC 1 minuto (Databento; se descarta el día si cambia el contrato). Coste 2,9 pb.
- EURUSD: HistData M1 (BID). Coste 1,1 pb.
6 pruebas (3 eventos × 2 mercados).

## Criterio
Por prueba: media bruta > 0 con t (Newey-West) ≥ 2,64 (Bonferroni unilateral 0,05/6 con margen por la muestra pequeña:
se usa t ≥ 2,64, no 2,39); media > 0 en las dos mitades (NFP y comunicado: hasta 2019 / desde 2020; rueda de prensa: 2019-22 / 2023-26);
media neta de costes > 0 en la segunda mitad. Lo que pase → candidata que necesitaría segunda fuente (contado XAUUSD) y medir
el spread real a esa hora en FTMO. Lo que falle → cerrado sin variantes. Informativo: la reversión (signo contrario).
Contador +6.
