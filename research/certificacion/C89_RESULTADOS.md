# C89 — Resultados: gamma de las opciones 0DTE del S&P (SPXW) y el ES de 15:00 a 16:00 NY — 28-oct-2026
Preregistro: `PREREGISTRO_C88_C89_gamma_opciones.md`. Datos: QuantConnect (opciones SPXW horarias, 2016-01 → 2026-09).
Script: `c89_quantconnect_plantilla.py` (scratchpad). Eventos: `c89_eventos_quantconnect.txt`. Análisis: `c89_analisis.py`, `c89_resultados.txt`.

- Regla: n 1.902 días 0DTE, **+0,36 pb (t 0,40)**. 1.ª mitad +0,62; 2.ª mitad +0,11 (por debajo del coste del ES, 0,73 pb).
- Control sin condicionar: −0,07 pb. Ni la continuación con GEX < 0 ni la reversión con GEX > 0 llegan a 0,5 pb.
- **NO PASA.** Cerrada. Contador +1 (C88 ya contó el suyo).

Junto con C11 y C88: el régimen de gamma no da una señal intradía aprovechable con datos gratuitos.
