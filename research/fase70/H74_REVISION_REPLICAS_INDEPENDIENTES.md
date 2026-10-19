# H74 Noise Area — revisión de réplicas independientes y veredicto (19-oct-2026)

## 1. Brusco, `giovannibrusco/zarattini-2024-momentum-spy` (GitHub, último commit 16-oct-2026) — leído completo
Clonado y leído (README, `docs/SPEC.md`, `docs/CONCLUSIONS.md`, `reports/validation*.md` y las partes
relevantes de `src/`). No se ha ejecutado su código (contenido externo; sus datos brutos no se
redistribuyen).

**Reglas frente a nuestra implementación (H74):**
| Elemento | Brusco | Nuestra H74 | Efecto esperado |
|---|---|---|---|
| σ por minuto, 14 días, \|P/Open − 1\| | igual | igual | — |
| Bandas ancladas a max/min(Open, cierre previo) | igual | igual | — |
| Controles a HH:00/HH:30, 10:00-15:30 | igual | igual | — |
| Precio de decisión | cierre de la vela de HH:MM | cierre de la vela que termina en HH:MM | igual en la práctica |
| **Precio de ejecución** | ese mismo cierre | **apertura del minuto HH:MM** (como el experimento real de los autores) | diferencia de 1 minuto, menor |
| **VWAP** | precio típico (H+L+C)/3 × volumen; con SPY usa el feed IEX (~3% del volumen) → VWAP aproximado | precio medio de cada vela de IB × volumen consolidado | menor: validado por Brusco con ES (corr. 0,97) |
| Salida final | max(VWAP, banda) / min(VWAP, banda) | igual | — |
| Tamaño | 2%/σ14, tope 4x | igual | — |
| Cierre forzoso | 15:59 | 16:00 (cierre de la última vela) | igual |
| Costes | SPY 0,0035 $/acción sin deslizamiento; ES 0,85 $ + 1,40 $ por contrato y lado + 0,25 tick (≈0,4 pb por ida y vuelta) | 0,0045 $/acción | — |

**Resultados que publica (no verificados por nosotros):**
- SPY (Alpaca IEX) 2020-07 → 2026-07: Sharpe 1,11, alfa 16,7% (t=2,85). Por años: 2020 +9,2%,
  2021 +30,6%, 2022 +25,8%, 2023 +29,3%, 2024 +24,8%, **2025 −4,9% (SR −0,27), 2026 hasta julio −12,9% (SR −1,91)**.
- ES (IB, contrato continuo propio) 2024-05 → 2026-07: variante final **Sharpe −0,07**, CAGR −2,1%, t del
  alfa 0,1. Mismo período SPY frente a ES: correlación diaria 0,97. Con 0,25-1 tick de deslizamiento
  sigue negativo: **el problema es la señal, no los costes ni el feed**.
- Rejilla de 27 variantes (con protocolo previo y DSR): gana la configuración original; el
  walk-forward trimestral destruye valor (Sharpe 0,57 frente a 0,92).
- Su propia conclusión: "no asignable hoy"; no pasa a la fase de prop firm.

## 2. Delgado, "Beat the Market Revisited" (SSRN 7323419) — NO LEÍDO
SSRN devuelve HTTP 403 a esta sesión en todas sus rutas (página, descarga, API) y el artículo no
aparece en ningún índice ni buscador accesible. **No puedo confirmar su contenido**, ni si informa de
resultados posteriores a la publicación, ni su significación. Si el usuario puede descargar el PDF y
subirlo al repo, se analizará.

## 3. Otras evidencias posteriores a la publicación
- Los propios autores (FAQ Q24 de la versión de feb-2025): mayo-dic 2024 ≈ +15% y enero-2025 −1,2%.
  Autodeclarado, no independiente.
- Mesfin (arXiv 2605.04004 v3, sep-2026), MNQ 2021-2025: ninguna de 14 familias de momentum intradía
  OHLCV supera sus 5 criterios tras costes (no es esta estrategia exacta, pero es la misma familia y
  mercado afín).

## 4. Significación de la evidencia reciente
Con Sharpe ≈ 0 en 2025-2026 en dos fuentes independientes (SPY y ES con VWAP real) y nuestro propio
análisis de costes (equilibrio ≈ coste de CFD), el período posterior a la publicación (may-2024 →
jul-2026, ~2,2 años) arroja en conjunto un rendimiento cercano a cero. No hay evidencia fuera de
muestra significativa a favor; tampoco basta para declararla muerta (el paper muestra pausas largas en 2012-2015).

## 5. Veredicto
**Noise Area queda DESCARTADA como candidata actual** (criterio fijado por el usuario: sin ventaja
reciente). Se mantiene solo como seguimiento congelado a futuro (reglas de H74 sin cambios). No se
descargarán datos de Alpaca solo para esta estrategia; las instrucciones quedan preparadas en
`research/fondeo/INSTRUCCIONES_ALPACA.md` para hipótesis futuras que necesiten SPY/QQQ en 1 minuto con volumen.
