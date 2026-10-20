# C3 — Réplica fiel de Breedon & Ranaldo con FXCM 2012-2026: RESULTADOS (20-oct-2026)

Pre-registro: `PREREGISTRO_C3_breedon_ranaldo.md` (commit e1981e1, antes de descargar). Salida: `c3_resultados.txt`,
`c3_costes_cartera.txt`. Código: `c3_breedon_ranaldo.py`. FXCM M1 punto medio, 2012-01 → 2026-09 (≈ 3.700 días por sesión).

| Par | Sesión | Signo previsto | Media (sentido previsto) | t | Años | Corr. HistData | Holm | Certificada |
|---|---|---|---|---|---|---|---|---|
| EUR/USD | Europa (07 Londres → 08 NY) | − | **+2,28 pb** | **5,08** | 13/15 | 0,98 | Sí | **Sí** |
| GBP/USD | Europa | − | **+1,65 pb** | **3,26** | 12/15 | 0,98 | Sí | **Sí** |
| USD/CHF | EE. UU. (08 → 16 NY) | − | +1,46 pb | 2,40 | 11/15 | — | No | No |
| EUR/USD | EE. UU. | + | +1,38 pb | 2,31 | 10/15 | 0,99 | No | No |
| GBP/USD | EE. UU. | + | +1,27 pb | 2,05 | 10/15 | 0,99 | No | No |
| USD/CHF | Europa | + | +0,92 pb | 1,42 | 10/15 | — | No | No |
| EUR/JPY | Europa | − | +0,07 pb | 0,10 | 7/15 | — | No | No |
| AUD/USD | EE. UU. | + | +0,05 pb | 0,08 | 7/15 | — | No | No |
| USD/JPY | EE. UU. | − | −0,96 pb | −1,52 | 3/15 | 0,99 | No | No |
| EUR/JPY | Japón | + | −0,82 pb | −1,84 | 4/15 | — | No | No |
| USD/JPY | Japón | + | **−1,43 pb** | **−3,17** | 4/15 | 0,99 | No | No (signo contrario) |
| AUD/USD | Australia | − | **−2,13 pb** | **−4,20** | 2/15 | — | No | No (signo contrario) |

## Lectura
- **Europa se mantiene 5-9 años después de la publicación**: euro y libra se deprecian en horario europeo.
- **Dólar débil en horario de EE. UU.**: del signo previsto en los tres pares (t 2,0-2,4), pero no supera la corrección
  por 12 pruebas. Muy correlacionadas entre sí (0,6-0,8): es un único factor, no tres.
- **Asia se ha invertido**: yen y dólar australiano se **aprecian** en su horario (t −3,2 y −4,2), al revés que en
  1997-2007. Es un hallazgo a posteriori; no se certifica (habría que comprobarlo con otros datos antes de usarlo).

## Costes y cartera (informativo, `c3_costes_cartera.txt`)
- Sesión europea EUR/USD 2012-2026, neta: Sharpe 1,08 / 1,02 / 0,87 con costes 0,44 / 0,53 / 0,79 pb; 13/15 años netos
  positivos; ventaja/coste 3,6-5,2. Pero en 2018-2026 se debilita (neto Sharpe 0,72 con coste bajo, t = 2,06) frente a la
  franja C1 06-08 (Sharpe 1,10, t = 3,12). Correlación entre ambas: 0,52.
- **Cartera EUR + GBP (sesión europea, igual riesgo): Sharpe bruto 1,24 frente a 1,33 del EUR solo** (correlación 0,50):
  la libra no diversifica, repite el mismo efecto con menos fuerza.

## Conclusión para el objetivo de cartera
Con las reglas del propio estudio, las ventajas que se mantienen están todas en la sesión europea y se mueven juntas.
No hay hoy una segunda ventaja certificada e independiente que suba el Sharpe de la cartera. La candidata más prometedora
para diversificar (correlación ≈ 0 con Europa) es el factor "dólar débil en horario de EE. UU.", que necesitaría una
certificación propia con datos no usados (p. ej. HistData 2008-2011, posteriores al estudio y no usados para esta sesión).
