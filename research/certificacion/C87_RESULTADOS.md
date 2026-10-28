# C87 — Resultados: "pinning" el día de vencimiento de las opciones mensuales de oro y crudo — 28-oct-2026
Reglas en PREREGISTRO_C87. Código QuantConnect `c87_quantconnect_plantilla.py`; eventos `c87_eventos_quantconnect.txt`.
Crudo: los tramos 2024-2026 fallaron en QuantConnect (sin resultados); muestra 2012-2023.

| | n | Media | t | Aciertos | ≤ 2018 | ≥ 2019 | Distancia media a K* | Veredicto |
|---|---|---|---|---|---|---|---|---|
| Oro (13:30) | 159 | −0,31 pb | −0,07 | 46 % | **+11,4 pb** (2012-18, todos los años ≥ 0 salvo 2016) | **−11,0 pb** (t −1,86) | 80 pb | NO PASA |
| Crudo (14:30) | 131 | −22,0 pb | −1,41 | 47 % | −35,1 | −3,4 | 71 pb | NO PASA |

Oro: el efecto de atracción hacia el strike existió hasta 2018 y desde 2019 se da la vuelta (el precio se aleja del strike), coincidiendo
con el auge del gamma de opciones a corto plazo y lo descrito para el S&P. Crudo: nunca hubo atracción. Cerrado. Contador +2.
