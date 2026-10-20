# E1 — Estrategia EURUSD 06:00 → 08:00 ET: RESULTADOS (20-oct-2026)

Pre-registro: `PREREGISTRO_E1_estrategia_eurusd.md` (commit 25d7300, antes de calcular). Código: `e1_peor_franja.py`,
`e1_estrategia.py`; salida completa: `e1_resultados.txt`. Serie 2018-2026 (1.973 días operados tras los 60 de arranque del
tamaño por volatilidad). **Costes todavía supuestos** (fuentes de terceros): el escenario real se fijará con la demo.

## Backtest 2018-2026 (sobre el capital, sin capitalizar)
| Riesgo | Coste | Rent. anual | Sharpe | t | DD máx. | Peor día | Años + | Stops |
|---|---|---|---|---|---|---|---|---|
| 0,5% | bajo 0,44 pb | 7,7% | 0,91 | 2,56 | −14,8% | −2,1% | 6/9 | 12 |
| 0,5% | medio 0,53 pb | 6,7% | 0,80 | 2,24 | −15,4% | −2,1% | 6/9 | 12 |
| 0,5% | alto 0,79 pb | 3,9% | 0,47 | 1,31 | −17,1% | −2,1% | 5/9 | 12 |
| 1,0% | bajo | 13,9% | 0,88 | 2,43 | −29,7% | −4,1% | 6/9 | 12 |
| 1,0% | medio | 12,1% | 0,76 | 2,12 | −30,8% | −4,1% | 6/9 | 12 |
| 1,0% | alto | 6,9% | 0,44 | 1,21 | −34,2% | −4,1% | 5/9 | 12 |

## Simulación de fondeo (5.000 simulaciones con incertidumbre de la ventaja; referencia = misma estrategia sin ventaja)
| Riesgo | Coste | FTMO 2-Step | FundedNext 2-Step | FundingPips 2-Step | Sin ventaja | Días hábiles (mediana) | Sobrevive 1 año financiada |
|---|---|---|---|---|---|---|---|
| 0,5% | bajo | **79,8%** | 80,5% | 80,5% | 31-36% | 278-334 | 94% |
| 0,5% | medio | 75,6% | 76,7% | 76,7% | 32-35% | 291-341 | 92-93% |
| 0,5% | alto | 59,2% | 62,1% | 62,1% | 31-36% | 324-393 | 89% |
| 1,0% | bajo | 59,0% | 60,1% | 60,1% | 28-34% | 100-124 | 58-72% |
| 1,0% | medio | 54,8% | 57,5% | 57,2% | 28-34% | 100-129 | 58-71% |
| 1,0% | alto | 43,3% | 46,7% | 47,2% | 28-34% | 104-133 | 54-63% |

Ningún escenario incumple el límite diario (el stop a 4 σ lo protege); todas las cuentas perdidas lo son por la pérdida
máxima del 10% (DD histórico de −15% con riesgo 0,5%).

## Lectura
- La estrategia duplica aproximadamente la probabilidad de superar la evaluación frente a la misma operativa sin ventaja.
- Es **lenta**: con riesgo 0,5% la mediana es de más de un año de días hábiles para superar las dos fases (FTMO no tiene
  límite de tiempo; comprobar en cada firma). Con 1% es 4-6 meses, pero la mitad de las veces se pierde la cuenta.
- El coste decide: con el escenario alto (FTMO 3 $ por lado) la ventaja deja de ser significativa (t = 1,3).
- Riesgos no modelados: que la ventaja se debilite (2024 y 2026 flojos), diferencias de ejecución reales a las 06:00 y 08:00
  ET, reglas de noticias de cada firma y que la firma permita EAs.
