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

## Actualización v3 (29-oct-2026): con Nikkei (C101) y cobre (C102); candidatas aparte
Composición A (firma normal, cierre 16:45): yen, cesta yen, oro viernes 16:45, oro D−2, Nikkei Q+2/Q−2, plata víspera 16:45 (E10b) +
diarias C93, C99, C101 NKD, C102 HG. B (permisiva): lo de B anterior + las mismas diarias. Candidatas sin confirmar: gas natural C95
(serie exportada de QuantConnect, coste 4 pb) y paladio C102 (Databento 1 h, coste 6 pb). **Todas las diarias al 20 % del riesgo
estándar (peso fijo, no optimizado).** Scripts: `escenario_carteras_v3.py`, `plan25_v3.py`, `mc_fondeo_v3.py`.

| | A confirmadas | A + candidatas | B confirmadas | B + candidatas |
|---|---|---|---|---|
| Sharpe 2018-26 | 1,98 | 1,97 | 2,24 | 2,26 |
| Riesgo/op para 25 % | 1,10 % | 1,01 % | 0,49 % | 0,47 % |
| Caída máx. histórica a 25 % | 22,1 % | 22,7 % | 15,8 % | 16,3 % |
| P(caída > 10 % en 1 año) | 24 % | 28 % | 12 % | 13 % |
| P(caída > 20 % en 8 años) | 14 % | 20 % | 3 % | 3 % |
| Fondeo al 15 %: aprueba 1.º / exámenes / pierde fondeada 24 m / retirado 24 m | 78 % / 2,2 / 55 % / 8.472 $ | 77 % / 2,3 / 59 % / 8.704 $ | 81 % / 1,8 / 43 % / 8.167 $ | 83 % / 1,8 / 42 % / 8.394 $ |
Las candidatas no aportan (gas: margen neto mínimo; paladio: coste alto). No se añaden.

## Si hubiera una firma de futuros con reglas tipo FTMO (`certificacion/mc_fondeo_ftmo_like.py`)
100.000 $, fase 1 +10 % y fase 2 +5 %, pérdida máx. 10 % fija y diaria 5 %, 500 $ por intento, retiro mensual 80 %. 24 meses.
| | Objetivo 25 %: riesgo/op | Aprueba a la 1.ª | Pierde la fondeada | Retirado 24 m | P(perder dinero) |
|---|---|---|---|---|---|
| A confirmadas | 1,10 % | 89 % | 25 % | 27.014 $ | 4 % |
| B confirmadas | 0,49 % | 89 % | 19 % | 26.401 $ | 3 % |
Búsqueda (29-oct-2026, blogs comparativos, sin verificar en las firmas): en futuros del CME casi todas usan pérdida arrastrada; las de 10 %
fijo son de CFD/forex (FTMO, FundedNext, FXIFY). Hay opciones fijas parciales (Phidias en evaluación —prohíbe bots según la revisión
anterior—; Purdia y For Traders fijas solo en la fondeada).

## Puntos 4 y 5 (29-oct-2026; `certificacion/puntos45.py`, `escen_comp.py`)
Punto 5 (quitar lo que no aporta): en A todas las estrategias suman (de +0,01 a +0,26). En B todas suman salvo bitcoin (−0,04): no por
mala, sino por exceso de tamaño (254 operaciones/año al 0,5 %). Con bitcoin al 20 %, como las demás diarias, B sube a 2,41 (decisión
tomada tras ver que restaba: optimista).
Punto 4 (reparto del riesgo; 2019-2026): control de volatilidad de la cartera (escala = vol. total / vol. de los 60 días anteriores,
limitada a 0,5-2; parámetros fijados sin probar alternativas):
| | Sharpe | Caída máx. al 25 % |
|---|---|---|
| A actual → con control de volatilidad | 1,99 → 2,12 | 21,4 % → 13,7 % |
| B (bitcoin 20 %) → con control de volatilidad | 2,51 → 2,69 | 20,3 % → 8,5 % |
Igual riesgo por estrategia con volatilidad pasada no mejora el Sharpe (A 1,79; B 2,35) aunque reduce la caída.
Fondeo típico (−4 % arrastrado) con A + control de volatilidad al 15 %: aprueba 82 %, 1,8 exámenes, pierde la fondeada 44 % en 24 m,
retira ~8.400 $. Tipo FTMO al 25 %: aprueba 96 %, pierde la fondeada 9 %, retira ~27.500 $ (100.000 $).
Aviso: el remuestreo por bloques de 20 días conserva solo en parte la dinámica de volatilidad.

## Versión intermedia (firma con cierre 16:50, p. ej. TradeDay) — `certificacion/escen_intermedia.py`
| | Sharpe | Con control de volatilidad | Caída al 25 % |
|---|---|---|---|
| A (salidas 16:45) | 1,98 | 2,11 | 13,9 % |
| Intermedia (oro y plata víspera hasta 16:50) | 1,92 | 2,10 | 14,4 % |
| + plata viernes recortada 16:30-16:50 (sin validar) | 1,32 | 1,44 | 22,5 % |
Los 5 minutos extra no aportan. Plata del viernes: 16:30-16:50 +1,77 pb frente a +4,9 pb hasta las 17:00 (lo bueno está en los últimos
10 minutos). La ventaja de B solo existe con salida a las 17:00, noches (materias primas) y bitcoin 17-19 NY.
