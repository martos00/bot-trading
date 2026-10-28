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

## Plan para el 25 % anual (28-oct-2026; `certificacion/plan_25_por_ciento.py`, bootstrap por bloques de 20 días sobre 2018-2026)
Carteras sin euro y con las dos del oro (C93 y C99, con el 15-25 % del riesgo estándar). A = firma normal (cierre 16:45), Sharpe 1,77.
E = firma que permite bots y mantener hasta las 17:00/de noche y cripto, Sharpe 2,15.

| Para 25 %/año | A | E |
|---|---|---|
| Riesgo base por operación | 1,45 % | 0,52 % |
| Caída máx. histórica 2018-26 | 31,8 % | 17,0 % |
| Peor año | −8,9 % (2026) | +7,5 % |
| 1 año simulado: mediana / 10 % peor | 25 % / 5 % | 24 % / 8 % |
| P(año negativo) | 5,9 % | 2,5 % |
| P(caída > 10 % en un año) | 32 % | 15 % |
| P(caída > 20 % en 8 años) | 48 % | 6 % |
| Cuenta de fondeo (−4 % arrastrado, objetivo 6 %): aprueba / tarda / quema en 1 año | 68 % / 1,5 meses / 42 % | 70 % / 2 meses / 35 % |
Más prudente en fondeo: E al 10 %/año (0,21 %/op.): aprueba 80 % en ~6 meses, quema 9 % al año.

## Ciclo completo en cuenta de fondeo de futuros (`certificacion/mc_fondeo_futuros.py`; 4.000 simulaciones de 24 meses)
Supuestos (cuenta típica, no de una firma concreta): 50.000 $, objetivo +6 %, pérdida máxima arrastrada 4 % (fin de día, se bloquea en el
saldo inicial), 150 $ por examen, fondeada con la misma regla, retiro mensual de lo que pase de +4 %, reparto 90 %. Sin límite diario ni
regla de consistencia. Con tope de 2.000 $ por retiro los resultados apenas cambian.

| Cartera B | Riesgo/op | Aprueba 1.er examen | Exámenes en 24 m | Meses a fondeada | Pierde la fondeada (24 m) | Retirado 24 m (media) | P(perder dinero) |
|---|---|---|---|---|---|---|---|
| 6 % | 0,12 % | 93 % | 1,0 | 11,0 | 1 % | 1.275 $ | 39 % |
| 10 % | 0,21 % | 91 % | 1,3 | 6,7 | 16 % | 4.489 $ | 11 % |
| 15 % | 0,31 % | 81 % | 1,9 | 4,3 | 46 % | 8.451 $ | 5 % |
| 25 % | 0,52 % | 68 % | 3,8 | 2,5 | 87 % | 15.838 $ | 2 % |
(Cartera A con el mismo objetivo: 86/83/76/67 % de aprobados; 1,2/1,7/2,6/4,9 exámenes; retirado 1.470/4.623/8.815/17.159 $.)
