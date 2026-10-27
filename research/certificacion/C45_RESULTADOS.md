# C45 — Resultados: confirmación independiente del oro el viernes 16:00 → 16:58 NY — 22-oct-2026
Reglas congeladas en PREREGISTRO_C45. HistData XAUUSD/XAGUSD M1 (contado, BID).

| | n | Media | t | Años + | 2010-17 | 2018-26 |
|---|---|---|---|---|---|---|
| **Oro viernes** | 782 | **+2,49 pb** | **3,78** | **14/17** | +3,45 pb (t 3,85) | +1,61 pb (t 1,71) |
| Plata viernes (inf.) | 780 | +3,25 pb | 2,79 | 14/17 | +5,16 pb (t 3,41) | +1,52 pb (t 0,88) |

Oro, misma hora otros días: lun +0,43 · mar +0,38 · mié −0,32 · jue +0,57 pb (todas |t| < 1,2): es un efecto del **viernes**.
Dentro de la hora: 16:00-16:29 +0,69 pb (t 1,85); **16:30-16:58 +1,77 pb (t 3,93)**.

**CONFIRMADA según los criterios fijados** (t ≥ 2, ≥ 60 % de años, 2018-26 > 0).
Aviso: en el contado el tramo reciente es más débil (+1,61 pb, t 1,71) que en el futuro (+3,86 pb). Posibles causas: el futuro incluye
los dos últimos minutos (16:58-17:00) o el BID del contado baja cuando se amplía el spread al cierre (sesgo en contra). Se comprueba
con el futuro a minuto (análisis descriptivo siguiente) antes de definir la estrategia.

## C45b — Futuro GC a minuto el viernes (descriptivo, Databento ≈ 0,4 $)
| Tramo | Media | t | 2010-17 | 2018-26 | Años + |
|---|---|---|---|---|---|
| 16:00 → 17:00 | +3,53 pb | 5,87 | +3,27 | +3,76 (t 4,24) | 15/17 |
| **16:00 → 16:55** | **+3,26 pb** | **6,09** | +3,28 | +3,25 (t 4,09) | **16/17** |
| 16:30 → 16:55 | +2,01 pb | 6,43 | +1,56 | +2,39 (t 4,72) | 15/17 |
| 16:55 → 16:58 | +0,22 pb | 1,63 | | | |
| 16:58 → 17:00 | +0,06 pb | 0,54 | | | |
El efecto NO depende de los últimos minutos. La debilidad reciente del contado de HistData (BID) no aparece en el futuro; lo más
probable es el sesgo del BID al ampliarse el spread por la tarde del viernes (va en contra del largo). Dispersión ≈ 15 pb por viernes:
Sharpe anual bruto ≈ 1,5; neto con 0,74 pb ≈ 1,2 (futuro); con CFD a 1-1,5 pb ≈ 0,9-1,1. Coste real del CFD pendiente de medir en MT5.


## Corrección 27-oct-2026 (hora de HistData)
El cargador trataba HistData como hora EST fija; en realidad viene en hora de NY con cambio de hora (comprobado contra FXCM: desfase de 60 min en verano). Repetido con la hora correcta (`c45_resultados_corregido.txt`): oro viernes 16:00→16:58 **+2,84 pb (t 4,80)**, 12/17 años, 2018-26 +2,76 pb (t 3,03): **sigue CONFIRMADA** (más fuerte en el tramo reciente). Plata: 2018-26 −1,57 pb (informativo).
