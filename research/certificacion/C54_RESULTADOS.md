# C54 — Resultados: confirmación independiente (HistData) de los hallazgos de fin de trimestre de B13 — 22-oct-2026
Reglas congeladas en PREREGISTRO_C54. (c45_oro_viernes.py se envolvió en `if __name__` para poder importar `carga()`; no cambia sus resultados.)
| Prueba | n | Media con su signo | t | Años | Resultado |
|---|---|---|---|---|---|
| 1a EURUSD Q+1 15-16 largo, 2012-26 | 49 | −0,03 pb | −0,03 | 7/15 | **NO PASA** |
| 1b EURUSD Q+1 15-16 largo, 2003-11 (fuera de periodo) | 29 | −0,03 pb | −0,03 | 4/9 | **NO PASA** |
| **2 EURJPY Q0 01-02 corto, 2012-26** | 59 | **+2,46 pb** | **2,86** | **10/15** | **PASA** |
| 3 WTIUSD Q−1 16-17 largo (inf. para HO) | 50 | +3,13 pb | 0,80 | 8/15 | sin apoyo |
- El euro del primer día del trimestre era un falso positivo de FXCM (otra fuente da cero en los mismos años y en 2003-11): descartado.
- **EURJPY corto el último día hábil del trimestre, 01:00-02:00 NY: confirmado.** Mecanismo candidato: repatriación japonesa al cierre del
  trimestre fiscal (01:00 NY = tarde de Tokio). Solo 4 operaciones al año.
- Gasóleo Q−1: sin fuente independiente y sin apoyo del crudo → no se certifica (podría ir a forward con riesgo mínimo).
