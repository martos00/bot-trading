# Auditoría: hora de HistData mal leída en `c45_oro_viernes.carga` — 27-oct-2026

**Fallo**: `carga()` (c45) trataba las marcas de HistData como EST fijo (UTC−5). En realidad vienen en **hora de Nueva York con
cambio de hora** (ya se sabía: README, H71). Comprobado contra FXCM (UTC): con EST fijo, HistData queda 60 min desplazado en verano y
0 en invierno (correlación de rentabilidades a 1 minuto 0,97-0,99 con el desfase correcto). En verano, cada ventana "hh:mm NY" medía en
realidad la hora anterior. Afectaba a C45, C49, C54, C55, C57, C58, C59, C60, C62, C64, B15, E8b y a `c74.cargar_histdata` (C74, C76, C77).
El resto de scripts con HistData ya usaba hora de NY. Se corrige `carga()` y se repite todo; salidas `*_resultados_corregido.txt`.

## Ventajas certificadas: todas siguen confirmadas (y casi todas más fuertes)
| Confirmación | Antes | Con la hora correcta |
|---|---|---|
| C45 oro viernes 16:00-16:58 (E8) | +2,49 pb (t 3,78); 2018-26 t 1,71 | **+2,84 pb (t 4,80); 2018-26 +2,76 (t 3,03)** |
| E8b oro 16:00-16:45, contado | +1,84 pb (t 3,76) | **+2,16 pb (t 5,03)** |
| C49 plata víspera (E10) | +5,15 pb (t 2,35) | +4,47 pb (t 2,19), 13/17 años: sigue confirmada |
| C54 EURJPY Q0 01-02 corto (E11) | +2,46 pb (t 2,86), 10/15 | **+4,33 pb (t 6,07), 14/15** |
| C55 yen Q0 frente a todos (E11) | t 4,52 | t 4,07: sigue |
| C57 USDJPY D−2 07-08 2003-11 (E9) | +1,76 pb (t 1,67) | **+1,95 pb (t 2,20)**; resto de días 0,08 |
| C58 USDJPY Q0 2003-11 (E11) | +4,42 pb (t 2,62) | **+7,68 pb (t 4,55), 9/9 años** |

## Descartadas antes que ahora salen positivas (SOLO HistData: no certificadas, requieren otra fuente y preregistro)
- **C54 1a — EURUSD largo el primer día hábil del trimestre (Q+1) 15:00-16:00 NY**: 2012-26 +2,33 pb (t 4,91), 13/15 años;
  pero 2003-11 −0,02 pb (t −0,01). Antes figuraba como "falso positivo".
- **C60 — Nikkei CFD (JPXJPY) largo el 2.º día hábil del trimestre 15:00-16:00 NY**: +16,2 pb (t 4,12), 15/16 años, 2018-26 +10,7
  (t 3,65). Antes "falso positivo por precio rancio del NKD". Ojo: a esa hora Tokio está cerrado (04-05 h) y el CFD puede tener
  precios poco fiables; necesita otra fuente.
- C64 dividendos japoneses (JPX 01-02): sube a t 1,48-1,94, sigue sin pasar Holm. C62 Brent/WTI: sigue "certificada" en HistData
  (t 2,40) pero ya se había descartado como artefacto del CFD. B15: sigue sin ninguna regla que pase.

## Pruebas de hoy afectadas
C74 (TJR): sigue sin pasar. C76: EURUSD tras el comunicado del FOMC pasaba en HistData pero FXCM no lo confirma. C77: ninguna pasa.
