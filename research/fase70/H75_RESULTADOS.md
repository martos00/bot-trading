# H75 — Timing del S&P 500 de Connors & Alvarez: resultados (SPY 1993-2026)

Detalle completo: `h75_resultados.txt` (métricas) y `h75_fondeo_oos.txt` (simulación de fondeo).

**Fidelidad:** Double 7's da 130 operaciones (1995-2007) y 188 (2008-2026), PF 3,37 y 2,36, coherente
con la réplica independiente de StrategyQuant (333 operaciones 1993-2026, PF 2,35). TRIN: no
reproducible (sin datos gratuitos).

**Fuera de muestra 2008-2026, neto de costes de CFD (spread + financiación):**

| Estrategia | Ops | % gan. | Media/op | t | PF | p vs entradas aleatorias | Veredicto pre-registrado |
|---|---|---|---|---|---|---|---|
| VIX Stretches | 127 | 76% | +0,19% | 0,82 | 1,33 | 0,39 | No |
| VIX RSI | 152 | 76% | +0,34% | 2,44 | 1,81 | 0,10 | No (no supera al azar) |
| Cumulative RSI | 188 | 72% | +0,31% | 2,65 | 1,75 | 0,12 | No (no supera al azar) |
| S&P Short | 25 | 76% | +0,85% | 1,59 | 2,62 | 0,05 | No (t < 2, pocas operaciones) |
| Double 7's | 188 | 77% | +0,54% | 3,73 | 2,00 | 0,12 | No (no supera al azar) |
| **RSI(2) < 5** | **80** | **79%** | **+0,53%** | **2,50** | **2,20** | **0,007** | **Cumple los 3 criterios** |

- El benchmark de entradas aleatorias se restringe a días con SPY por encima de su SMA200, como
  fija el pre-registro (una primera versión sorteaba entre todos los días; corregida antes de
  concluir).
- **Selección múltiple:** el DSR con N = 88 ensayos es ≈ 0 para todas. RSI(2) < 5 supera Bonferroni
  dentro de la familia (6 × 0,007 = 0,04), pero no a escala de todo el proyecto. Se considera
  **candidata débil**, no validada.
- **Fondeo (FTMO 2-Step / FundedNext, OOS):** con apalancamiento 1x, RSI(2) < 5 supera el 62-67% de
  las simulaciones pero tarda una mediana de 900-1.100 días hábiles; al apalancar, el incumplimiento
  de la **pérdida diaria** domina (55-79%), porque las entradas se concentran en ventas fuertes.
  Limitación: sin datos intradía, el mínimo diario se aproxima con el cierre (subestima el riesgo).
- **Compatibilidad:** las posiciones duran 3-7 días y cruzan fines de semana: solo cuentas tipo
  Swing o evaluaciones que lo permitan.

**Lección de diseño para fondeo:** las estrategias de "comprar caídas" necesitan un tamaño de posición
inversamente proporcional a la volatilidad (como el 2%/σ de Zarattini-Aziz-Barbon) para que el riesgo
diario no se dispare justo en los días de pánico. Esto será una hipótesis nueva y pre-registrada, no un
ajuste retroactivo de H75.
