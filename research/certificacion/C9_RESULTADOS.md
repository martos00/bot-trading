# Resultados C9 — Regla del 80% de Dalton (S&P 500 / Nasdaq 100, HistData M1 2010-2026)

Pre-registro: `PREREGISTRO_C9_regla_80_dalton.md` (commit b9c9094). Script `c9_regla_80_dalton.py`, salida `c9_resultados.txt`,
operaciones `c9_spx.csv`, `c9_nsx.csv`. Coste 1,0 pb por ida y vuelta.

| | S&P 500 2010-2017 | **S&P 500 2018-2026** | Nasdaq 2010-2017 | Nasdaq 2018-2026 |
|---|---|---|---|---|
| Operaciones | 279 | 370 | 364 | 406 |
| Neto por operación | 1,5 pb (t 0,64) | **5,1 pb (t 2,54)** | −1,7 pb (t −0,82) | 1,0 pb (t 0,36) |
| Bruto / coste | 2,5 | 6,1 | −0,7 | 2,0 |
| Años netos + | 4/7 | 7/9 | 3/8 | 5/9 |
| Llegan al objetivo | 50% | 55% | 46% | 49% |

**Los criterios pre-registrados se cumplen en el S&P 500** (descubrimiento > 0; confirmación t 2,54, 6,1× el coste, 7/9 años).

## Por qué NO se certifica todavía
1. **Sin fuente independiente:** solo HistData. FXCM no publica velas de índices; Dukascopy está limitado (≈ 84 ficheros/h).
2. **El Nasdaq 100, mismo mecanismo, no lo muestra** (t 0,36). Y en el descubrimiento del S&P era casi nulo (t 0,64).
3. **La "regla del 80%" no se cumple:** solo el 50-55% de las operaciones llega al objetivo.
4. Con ≈ 1.160 pruebas en el proyecto, una t de 2,5 aislada es compatible con suerte.

## Aunque fuera real, es pequeña
S&P 2018-2026, 42 operaciones al año: con un 1% de riesgo por operación, ≈ 2,9% al año (peor año −3,4%, caída máxima −8,3%),
Sharpe ≈ 0,6. Correlación con E1: 0,09 (diversificaría algo). Queda como **candidata débil**: solo merecería un forward test
o una comprobación con datos de otro proveedor (p. ej. el Probador de MT5 con US500).
