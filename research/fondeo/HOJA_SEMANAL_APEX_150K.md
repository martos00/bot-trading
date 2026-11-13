# Hoja semanal — Apex 150K EOD (operación a mano, sin rupturas)

Preparada el 13-nov-2026. Reglas confirmadas por el soporte de Apex (13-nov-2026). Volatilidades con datos hasta sep-2026; precios de
referencia de sep-2026 (oro 4.186 $, plata 60,7 $, USDJPY ~160, Nikkei ~60.000). **Recalcula los contratos con el precio del día** con la
fórmula de abajo. Hora de España = hora de Nueva York + 6 (válido hasta el 8-mar-2027).

## Reglas de Apex que afectan a la hoja
- Todo cerrado antes de las 16:59 NY (22:59 España). Se puede mantener de 18:00 a 03:00 NY.
- Contratos: 10 micros = 1 contrato; límite conjunto (examen 12; cuenta fondeada nivel 1: 4, nivel 2: 5, nivel 3: 7, nivel 4-5: 10).
- Límite de pérdida diaria: examen 2.000 $; fondeada 2.500 $ (3.000-4.000 $ en niveles altos). Si se toca, se pierde el día (no la cuenta).
- No hay micro yen (MJY): el yen solo con 6J (12,5 millones de yenes ≈ 78.000 $ por contrato).
- Toda operación con stop (bracket).

## Tamaño: riesgo 0,5 % en examen y en fondeada
Exposición = 0,5 % × 150.000 / σ (tope 6 × 150.000 = 900.000 $). Contratos = exposición / (precio × multiplicador); se redondea al entero
más cercano. Multiplicadores: MGC 10 oz, GC 100 oz, SIL 1.000 oz, SI 5.000 oz, 6J 12.500.000 ¥ / USDJPY, NKD 5 $ × índice.
Stop = 2 σ desde la entrada (dentro del límite diario); salida a la hora indicada si no salta antes.

| Operación | Mercado / sentido | σ de la franja | Exposición | Contratos (precios de ref.) | Stop (2 σ) | Pérdida si salta el stop |
|---|---|---|---|---|---|---|
| E8 oro viernes | MGC, COMPRA | 0,21 % | 357.000 $ | **9 MGC** (0,9) | −0,42 % ≈ −17,6 $/oz | ≈ −1.580 $ |
| Plata viernes | SIL, COMPRA | 0,28 % | 268.000 $ | **4 SIL** (0,4) | −0,56 % ≈ −0,34 $/oz | ≈ −1.360 $ |
| E10 plata víspera | SIL, COMPRA | 0,54 % | 139.000 $ | **2 SIL** (0,2) | −1,08 % ≈ −0,66 $/oz | ≈ −1.310 $ |
| E15 oro D-2 | MGC, VENTA | 0,41 % | 183.000 $ | **4 MGC** (0,4) | +0,82 % ≈ +34 $/oz | ≈ −1.370 $ |
| E9 yen D-2 | 6J, VENTA | 0,12 % | 625.000 $ | **8 6J** (examen) / **4** (nivel 1) / 5 (nivel 2) / 7 (nivel 3) | +0,24 % | ≈ −1.500 $ (8 contratos) |
| E11 yen fin de trimestre | 6J, COMPRA | 0,12 % (peso 1/3) | 208.000 $ | **3 6J** | −0,24 % | ≈ −500 $ |
| E13 Nikkei Q+2 | NKD, COMPRA | 0,40 % | 187.000 $ | **1 NKD** | −0,80 % ≈ −480 puntos | ≈ −2.400 $ (1 contrato es más que el tamaño ideal) |
| E16 Nikkei Q-2 | NKD, VENTA | 0,48 % | 156.000 $ | **1 NKD** | +0,96 % ≈ +580 puntos | ≈ −2.900 $ → usa stop de 380 puntos (≈ −1.900 $) |
| C113 oro madrugada (opcional) | MGC, COMPRA | 0,50 % (peso 0,2) | 30.000 $ | **1 MGC** | −1,0 % ≈ −42 $/oz | ≈ −420 $ |

Viernes: oro y plata se solapan de 16:30 a 16:55 NY. Si saltaran los dos stops el mismo día serían ≈ −2.900 $ (por encima del límite del
examen: Apex cortaría el día en −2.000 $). En el examen puedes bajar la plata a 3 SIL.

## Calendario (hora España; NY = España − 6)
| Fecha | Operaciones |
|---|---|
| Domingo a jueves (cada noche) | C113: comprar 1 MGC a las 00:00, cerrar a las 09:00 (opcional; no la noche antes de festivo ni el 31-dic) |
| **Vie 20-nov** | Oro 22:00→22:55 (9 MGC) · Plata 22:30→22:57 (4 SIL) |
| Mié 25-nov | Plata víspera de Acción de Gracias 22:00→22:55 (2 SIL) |
| Jue 26-nov (Acción de Gracias) | Yen D-2 13:00→14:00 y oro D-2 15:30→16:00 según la regla, pero con el mercado de EE. UU. en festivo (poca liquidez y horario reducido): **mejor no operar** |
| Vie 27-nov | El CME cierra antes ese día: **no hay oro ni plata del viernes** |
| Vie 4-dic | Oro 22:00→22:55 · Plata 22:30→22:57 |
| Vie 11-dic | Oro · Plata. **Buen momento para empezar exámenes** (cubren el cambio de trimestre) |
| Vie 18-dic | Oro · Plata |
| Jue 24-dic | El CME cierra antes: **no hay plata de víspera** |
| Vie 25-dic | Festivo: sin operaciones |
| **Mar 29-dic** | Yen D-2: vender 6J 13:00→14:00 · Oro D-2: vender 4 MGC 15:30→16:00 |
| **Jue 31-dic** | Yen fin de trimestre: comprar 3 6J 06:30→08:00 · Nikkei Q-2: vender 1 NKD 02:00→03:00 (madrugada del 30 al 31) |
| Vie 1-ene | Festivo: sin operaciones |
| **Mar 5-ene** | Nikkei Q+2: comprar 1 NKD 21:00→22:00 |
| Vie 8-ene | Oro · Plata |
| Viernes siguientes | Oro · Plata cada viernes (salvo festivo o cierre anticipado) |

## Antes de cada operación
1. Mira el calendario económico: no abras ni cierres en los 2 minutos de una noticia de alto impacto.
2. Recalcula los contratos con el precio del día si se ha movido más de un 10 % respecto a los de referencia.
3. Pon la orden a mercado con bracket (stop a 2 σ; sin objetivo) y cierra a mano a la hora de salida.
4. Con copiador: la orden en la cuenta principal se replica en las demás.
5. Apunta la entrada, la salida y el resultado (sirve para comparar con el backtest).
