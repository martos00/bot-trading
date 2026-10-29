# Guía: cartera para Tradeify (B sin bitcoin ni cesta), cuenta de 50.000 $ — 29-oct-2026
Scripts: `certificacion/cartera_tradeify.py`, `certificacion/mc_tradeify.py`. Backtest 2018-03 → 2026-09 con control de volatilidad.

## Qué opera
| Estrategia | Cuándo (NY) | Operaciones/año | % del beneficio |
|---|---|---|---|
| Oro viernes (MGC) | viernes 16:00 → 16:55, largo | 48 | 38 % |
| Plata viernes (SIL) | viernes 16:30 → 16:57, largo | 48 | 29 % |
| Plata víspera de festivo (SIL) | 16:00 → 16:55, largo | 9 | 12 % |
| Yen fin de mes (MJY) | antepenúltimo laborable 07:00 → 08:00, corto | 12 | 12 % |
| Oro D−2 (MGC) | antepenúltimo laborable 09:30 → 10:00, corto | 12 | 8 % |
| Yen fin de trimestre (MJY) | último laborable del trimestre 00:30 → 02:00, largo | 4 | 2 % |
Total ~133 operaciones/año en ~64 días. Sharpe 2,22.

## Riesgo y resultados (backtest)
| Objetivo | Riesgo base/op | Caída máx. | Peor mes | Peor día | 2025 / 2026 |
|---|---|---|---|---|---|
| 10 % | 0,28 % | 5,3 % | −2,5 % | −2,1 % | +3,3 % / +3,9 % |
| 15 % | 0,42 % | 7,9 % | −3,8 % | −3,1 % | +5,0 % / +5,8 % |
| 25 % | 0,69 % | 13,1 % | −6,4 % | −5,2 % | +8,3 % / +9,7 % |
Meses negativos 34 %; la racha más larga sin nuevos máximos, ~12 meses (2018-19).

## Cuenta de fondeo (50K, objetivo +6 %, −4 % arrastrado fin de día, 145 $, retiro mensual 90 %; 24 meses)
| Riesgo/op | Backtest: aprueba / exámenes / pierde fondeada / retirado | Si el Sharpe real es el 60 %: ídem |
|---|---|---|
| 0,28 % | 95 % / 1,1 / 9 % / 4.468 $ | 76 % / 1,5 / 22 % / ~1.900 $ |
| 0,42-0,46 % | 87 % / 1,6 / 34 % / 8.459 $ | 64 % / 2,8 / 69 % / ~4.900 $ |
| 0,69 % | 76 % / 3,0 / 79 % / 16.313 $ | 57 % / 4,7 / 93 % / ~9.000 $ |

## Comparación: Elite Trader Funding 150K «en vivo» (condiciones pegadas por el usuario, 29-oct-2026; `certificacion/mc_150k.py`)
Objetivo 9.000 $, pérdida máx. 5.000 $ arrastrada en vivo (incluye beneficio abierto: la simulación diaria es optimista), sin límite
diario, cuota 30 días 34,70 $ (promoción) o 347 $, activación 247 $, retiro máx. 2.250 $/pago. Cartera 150K sin bitcoin (Sharpe 2,34).
- 0,25 %/op: aprueba 93 %, pierde fondeada 11 %, neto 2 años +11.700 $ (cuota 34,70) / +8.800 $ (347); Sharpe al 60 %: +4.300 $ / −80 $.
- 0,30 %/op: aprueba 89 %, pierde fondeada 19 %, neto +15.800 $ / +13.300 $; Sharpe al 60 %: +6.500 $ / +2.700 $.
Condiciones: ETF prohíbe bots salvo aprobación escrita; en planes que no son Diamond Hands hay que cerrar 1 minuto antes del cierre del
instrumento (≈ 16:59 en metales). Diamond Hands 100K (3,5 % / 1,5 % diario, cuota mensual): peor (`mc_etf.py`).
- Objetivo 25 %/año en ETF 150K (0,65 %/op; `mc_150k_25.py`): peor día histórico −6.983 $ (> límite de 5.000 $); aprueba al 1.er intento
  39 %; ~2,4 intentos; pierde la fondeada en < 12 meses 40 %; neto 2 años ~+28.000-30.000 $ (backtest). Mismo riesgo con Sharpe real al
  60 %: aprueba al 1.º 13 %, ~4,6 intentos, pierde la fondeada en < 12 m 67 %, neto +15.000-18.000 $, P(perder dinero) 8-20 %.
  El tope de 2.250 $/pago limita lo retirable a ~24.300 $/año. Simulación diaria: el arrastre en vivo real es más duro.
