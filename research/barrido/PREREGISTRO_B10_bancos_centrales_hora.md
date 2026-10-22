# Pre-registro B10 — Barrido "día de banco central × hora" en 30 futuros y 13 divisas — 22-oct-2026
Redactado y enviado a git ANTES de calcular.
## Fechas
FOMC: scratchpad n/fomc.csv (días de anuncio). BCE: eampd.xlsx, hoja "Press Conference Window" (Euro Area Monetary Policy Event-Study
Database), hasta su última fecha. Tipos de día: FOMC−1, FOMC, FOMC+1, BCE−1, BCE, BCE+1 (días hábiles con datos del propio mercado).
## Regla y criterios
Futuros: mismos 30 mercados, datos y costes que B7 (b7_cambio_mes_hora.py), descubrimiento 2010-06 – 2017, confirmación 2018 – 2026-09.
Divisas: mismos 13 pares, precios y costes reales que B9 (b9_calendario_hora_divisas.py), descubrimiento 2012-2018, confirmación 2019 – 2026-09.
Franjas de 1 h (sin 17-18 NY en futuros; sin 16-18 en divisas). Selección |t (NW)| ≥ 3,5 y n ≥ 50. Confirmación: (1) t ≥ Bonferroni
unilateral 0,05/k_sel (por separado en futuros y divisas); (2) ≥ 60 % de años con el signo; (3) bruto ≥ 3 × coste.
Aviso: la hora del anuncio (14:00 NY FOMC; 07:45/08:15 NY BCE) tiene mucha volatilidad y el signo del anuncio no es predecible: se espera
que esas celdas no pasen. Lo que pase necesita otra fuente. Contador + nº de reglas.
