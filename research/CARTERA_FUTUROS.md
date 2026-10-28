# Cartera para cuenta de fondeo de FUTUROS — composición decidida (28-oct-2026)

Decisión del usuario (28-oct-2026): **se quita el euro (E1)** de la cartera de futuros. Motivo: Sharpe propio 0,62, apenas diversifica
y es la causa del 2026 negativo; sin él la cartera mejora en Sharpe y caída. (La decisión se toma sobre el conjunto, no para retocar una regla.)
E1 sigue en el EA de FTMO (CFD), que queda aparcado.

## Composición (escenario E: firma que permite bots y mantener hasta las 17:00 NY / de noche)
Yen (E2/E11), cesta del yen fin de mes, materias primas en víspera de festivo (E12), oro viernes 16:00-16:55, oro D−2 09:30-10:00 (corto),
Nikkei Q+2 (largo) y Q−2 (corto), plata víspera de festivo 16:00-16:55, plata viernes 16:30-17:00, bitcoin 21-23 UTC (MBT, días laborables).
Pendiente de forward: C93 oro ruptura del día anterior (con euro no sumaba: 2,04 → 2,01-2,05; sin euro no calculado).

## Backtest 2018-03 → 2026-09 (0,5 % de riesgo por operación en cada estrategia; script `certificacion/escenario_cartera_futuros.py`)
| | Con euro | Sin euro |
|---|---|---|
| Sharpe | 2,04 | 2,10 |
| Rentabilidad anual | 28,1 % | 22,9 % |
| Caída máxima | 25,2 % | 16,8 % |
| 2026 (hasta sept.) | −2,7 % | +5,4 % |
| Escalado a caída máxima 5 % | 5,6 %/año | 6,8 %/año |
| Escalado a caída máxima 10 % | 11,2 %/año | 13,6 %/año |

Recordatorio: la caída máxima de 8,5 años es mayor que la de un año típico; es la cifra a usar con los límites de las firmas.
