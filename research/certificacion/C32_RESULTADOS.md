# Resultados C32 — Ideas de Google: London Fix, Frankfurt breakout, cointegración SEK/NOK: NINGUNA CERTIFICADA

Pre-registro `PREREGISTRO_C32_google_fix_frankfurt_coint.md`; script `c32_google.py`; salida `c32_resultados.txt`.
FXCM BID/ASK reales (L, F); HistData cierres 16:00 NY (P).

| Idea | Descubrimiento (neto) | Confirmación 2019-26 (neto) | Veredicto |
|---|---|---|---|
| London Fix (corto 15:45-16:00, largo 16:00-16:15) | −0,9 pb (t −3,47) | **−1,5 pb (t −5,37)**, 0/8 años; bruto +0,3 pb frente a 1,8 pb de coste | Pierde con seguridad |
| Frankfurt breakout (rango 06-07 UTC, 07-09 UTC) | +0,6 pb (t 1,84) | **+0,6 pb (t 2,12)**, 7/8 años; bruto 1,5 pb, coste 0,95 pb | No supera Holm ni 3× coste |
| Cointegración EUR/SEK–EUR/NOK | +2,9 pb (36 op.) | −6,9 pb (38 op.) | Sin ventaja (bruto 3 pb frente a 10 pb de coste) |
El Frankfurt breakout es positivo y estable, pero pequeño: con costes de FTMO apenas queda nada. Descartadas.

**Nota (revisión tras C33):** en el Frankfurt breakout la entrada se simuló al nivel de ruptura aunque el cierre de ese minuto
ya estuviera más allá (mismo sesgo a favor que en C33). Su +0,6 pb neto es, por tanto, un máximo; corregido sería menor.
El veredicto (no certificada) no cambia.
