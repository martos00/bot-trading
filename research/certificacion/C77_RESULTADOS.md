# C77 — Resultados: momentum de horas tras EIA (WTI) y tras noticias (EURUSD) — 27-oct-2026
Reglas congeladas en PREREGISTRO_C77 (commit 0f77600). Script `c77_momentum_horas.py`; segunda fuente `c77b_fomc_eurusd_fxcm.py`.

**Aviso**: la primera ejecución trataba HistData como hora EST fija y daba "EURUSD tras FOMC 14:05→16:00: +13,1 pb (t 3,47), 14/14 años,
PASA". Al confirmarlo con FXCM no coincidía (+3,0 pb, t 0,65); la causa era el desfase de 60 min de HistData en verano. Con la hora correcta:

| Prueba | n | Media | t | Antes de 2020 | Desde 2020 | Veredicto |
|---|---|---|---|---|---|---|
| WTI tras EIA (T+5 → 14:30) | 672 | −2,58 pb | −0,46 | −7,92 | +9,84 | NO PASA |
| EURUSD tras NFP (08:35 → 12:00) | 190 | −0,73 pb | −0,32 | +0,63 | −2,78 | NO PASA |
| EURUSD tras FOMC (14:05 → 16:00) | 103 | +6,04 pb | 1,48 | +13,02 | −1,96 | NO PASA |
FXCM (EURUSD tras FOMC): +3,04 pb (t 0,65), desde 2020 −6,88 pb. **Ninguna certificada. Cerrado.** Contador +3.
