# E8 — Resultados: estrategia oro del viernes 16:00 → 16:55 NY — 22-oct-2026
Reglas congeladas en PREREGISTRO_E8. GC.v.0 1 min (Databento). Riesgo 0,5 % por operación (vol. de 52 viernes), stop a 4 desviaciones.

Robustez 2011-26: mediana +2,39 pb, 59 % de viernes positivos, media recortada al 5 % +2,80 pb, desviación 11,4 pb.

| Coste | 2011-26 | 2018-26 |
|---|---|---|
| 0,74 pb (futuro) | 6,2 %/año, Sharpe 1,46, DD −8,9 %, 12/16 años | 6,6 %/año, Sharpe 1,55, DD −7,0 %, 7/9 |
| 1,5 pb (CFD provisional) | 4,1 %/año, Sharpe 0,96, DD −15,9 % | 4,3 %/año, Sharpe 1,02, DD −10,2 % |
| 2,5 pb | 1,3 %/año, Sharpe 0,30 | 1,4 %/año, Sharpe 0,33 |

**Cartera E1 + oro (2018-26, misma volatilidad que E1 solo al 0,5 %; correlación 0,03):**
| E1 | Oro | Cartera |
|---|---|---|
| FTMO 0,79 pb: Sharpe 0,54 | 0,74 pb | 9,4 %/año, **Sharpe 1,14**, DD −16,7 % |
| FTMO 0,79 pb | 1,5 pb | 7,6 %/año, Sharpe 0,92 |
| bajo 0,44 pb: Sharpe 1,00 | 0,74 pb | 12,7 %/año, **Sharpe 1,53**, DD −14,7 %, 8/9 años |
| bajo 0,44 pb | 1,5 pb | 10,9 %/año, Sharpe 1,31 |

Avisos: (1) el resultado depende mucho del coste real: por encima de ~2 pb ida y vuelta deja de merecer la pena; medirlo con
`MQL5/Scripts/Medir_Costes_Oro_Viernes_Gas_Jueves.mq5`. (2) La exposición media es 5,4 veces el capital (vol. de 1 h muy baja): comprobar
el apalancamiento máximo de metales de la cuenta (FTMO estándar 1:9) y limitar el tamaño a ese máximo. (3) Siguiente paso: demo/forward junto con E2.
