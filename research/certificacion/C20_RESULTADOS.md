# Resultados C20 — "Divisa local débil en su horario" en SEK, NOK, PLN, HUF, ZAR y TRY

Pre-registro `PREREGISTRO_C20_breedon_ranaldo_otras_divisas.md` (antes de descargar). Script `c20_otras_divisas.py`; salida
`c20_resultados.txt`. HistData M1 BID 2010-2026, USD/xxx de 07:00 Londres a 08:00 NY.

**Factor (media de los 6): 2010-2017 +3,5 pb/día (t 4,34), 8/8 años; 2018-2026 +2,4 pb/día (t 3,17), 8/9 años → CUMPLE el
pre-registro.** El mecanismo de la ventaja del euro se extiende a otras divisas europeas.

| Par | 2010-2017 | 2018-2026 | Holm | Resto del día 2018-26 | Corr. con EUR/USD sesión europea |
|---|---|---|---|---|---|
| USDPLN | +5,1 pb (t 4,98) | **+3,6 pb (t 4,05)**, 9/9 años | Sí | −2,6 pb (t −2,55) | 0,79 |
| USDHUF | +4,8 pb (t 4,08) | **+4,9 pb (t 4,15)**, 9/9 años | Sí | −3,4 pb (t −2,98) | 0,73 |
| USDTRY | +3,9 pb (t 3,85) | +4,5 pb (t 3,61) | Sí | **+5,3 pb (t 4,12)** | 0,05 |
| USDSEK | +1,7 pb (t 1,96) | +1,6 pb (t 1,91) | No | −0,8 pb | — |
| USDNOK | +2,6 pb | −0,7 pb | No | — | — |
| USDZAR | +3,8 pb | +0,8 pb | No | — | — |

Lectura (comprobaciones posteriores, no pre-registradas):
- **PLN y HUF:** efecto genuino de sesión (el dólar sube en horario europeo y devuelve parte el resto del día), más grande que
  en el euro (≈ 4-5 pb frente a ≈ 2,3 pb), estable 17 años. Pero se mueven con el EUR/USD (correlación 0,73-0,79): es casi la
  misma ventaja, con poca diversificación (correlación con E1 0,33-0,39).
- **TRY:** no es un efecto de sesión: la lira se deprecia igual el resto del día (tendencia de devaluación). Descartada.
- **Costes:** solo hay BID. Spreads de referencia (sin medir) ≈ 4-5 pb para PLN/HUF ≈ la ventaja bruta. Paso obligatorio antes de
  operar: medir el spread real de USDPLN/USDHUF a las 07:00 Londres y 08:00 NY en la cuenta (script de costes de MT5).
**Veredicto: certificada en bruto (PLN y HUF); operabilidad pendiente de medir costes reales; diversificación limitada.**
