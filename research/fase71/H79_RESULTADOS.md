# H79 — ORB de 15 min en MNQ (bot del usuario): RESULTADOS

Pre-registro: `PREREGISTRO_H79_orb15_mnq_usuario.md` (commit 3e0bd98, antes de cualquier cálculo). Salida: `h79_resultados.txt`.
Datos: HistData NSXUSD M1 2010-01 → 2026-09, 3.629 operaciones; hueco de feb-2017 excluido. Dos motores
(`h79_motor.py`, `h79_motor_independiente.py` en Python puro): **P&L idéntico día a día (diferencia 0 $)**.

| Escenario | P&L 2010-2026 | Media/día | t_NW | PF | Aciertos | DD máx |
|---|---|---|---|---|---|---|
| Bruto (sin costes) | +25.287 $ | +7,0 $ | 1,34 | 1,05 | 35% | −15.843 $ |
| **Neto base** (1 tick + 1,50 $/contrato) | **−83.453 $** | −23,0 $ | −4,24 | 0,86 | 35% | −106.174 $ |
| Neto estrés (2 ticks + 2,50 $) | −168.979 $ | −46,5 $ | −8,11 | 0,75 | 35% | −184.613 $ |

Por tramos (neto base): 2010-2015 −66.931 $ (22 contratos de mediana) · 2016-2020 −33.242 $ · **2021-2026 +16.719 $
(t = 1,64, PF 1,10, 2 contratos de mediana)**. Años positivos: 8 de 17.

**Control de dirección aleatoria:** p = 0,23. Entrar en la dirección de la ruptura no es mejor que tirar una moneda
en el mismo momento con el mismo stop y objetivo; siempre largo o siempre corto dan casi lo mismo (−26 $/día).

**Por qué los costes lo hunden:** la ganancia media es 0,56 puntos (1,12 $) por contrato, menor que la comisión
(1,50 $). Con tamaño en dólares fijo, cuando el rango es pequeño en puntos (NQ barato antes de 2016) el bot opera
muchos contratos y la comisión domina. Con NQ en niveles actuales opera ~2-3 contratos y el coste pesa menos.

## Fondeo (Monte Carlo con incertidumbre de la ventaja)
| Datos usados | Topstep 50K: supera | (con ventaja 0) | FTMO 2-Step: supera | (con ventaja 0) |
|---|---|---|---|---|
| 2010-2026 (regla del pre-registro) | **16,5%** | 39,3% | 3,8% | 32,0% |
| Solo 2021-2026 (complementario) | 57,1% | 37,6% | 70,0% | 31,3% |

Nunca toca el límite diario (peor día −0,92%); todas las cuentas perdidas son por la pérdida máxima (rachas de hasta
14 pérdidas seguidas con un 35% de aciertos).

## Veredicto: NO es candidata
No cumple ningún criterio pre-registrado: neto negativo con t = −4,2 en el período completo, 8/17 años positivos, y el
tramo reciente (+16.719 $) tiene t = 1,64, muy lejos de t ≥ 3. La dirección de la ruptura no aporta nada frente al
azar (p = 0,23). El resultado de 2021-2026 es elegido después de ver los datos y no está validado: con t = 1,64 es
compatible con suerte. No se ha modificado ninguna regla. N acumulado = 94.
