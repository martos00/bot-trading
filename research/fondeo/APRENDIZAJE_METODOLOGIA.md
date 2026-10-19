# Aprendizaje metodológico aplicado al proyecto (oct-2026)

Cada idea se clasifica como **[E]** respaldada por evidencia verificable, **[S]** fuente secundaria
(resumen o reseña, no he leído el original) u **[O]** opinión o recomendación sin evidencia publicada.

## 1. Material educativo recibido (TikToks de @alxquant y @cototrades)
Son guías de proceso, no estrategias. Todas sus recomendaciones son **[O]**, aunque coinciden con la
literatura. Lo que ya cubríamos: datos de calidad, costes realistas, ejecución en la siguiente vela,
sin look-ahead, benchmark, in-sample frente a out-of-sample, estrés de costes, sencillez y pocos
parámetros. Lo que **faltaba y se ha añadido o se añadirá**:
- Monte Carlo / bootstrap de la secuencia de resultados → `simulador_fondeo.py` (hecho).
- Simulación específica de evaluaciones de prop firm → `simulador_fondeo.py` (hecho; el nombre del
  cuaderno "PropFirm_MonteCarlo" de la imagen de @alxquant inspiró esto).
- Estabilidad de parámetros y walk-forward: solo tiene sentido cuando optimizamos parámetros. En las
  reproducciones fieles no hay nada que optimizar; se aplicará a las hipótesis propias que tengan
  parámetros libres (ver PBO más abajo).
- Paper trading / incubación y conciliación entre backtest y ejecución real: pendiente para cualquier
  candidata que llegue a EA.
- Límites diarios de pérdida, de operaciones y "guardarraíles" (máx. 4 operaciones/día, máx. 2
  pérdidas/día, sin posiciones a las 15:55 ET, visibles en una de sus imágenes): son controles de
  riesgo del bot, no fuente de ventaja.

## 2. Literatura cuantitativa verificada
| Concepto | Fuente | Aplicación al proyecto |
|---|---|---|
| Las anomalías publicadas pierden ~26% fuera de muestra y ~58% tras publicarse **[S]** | McLean & Pontiff, JF 2016 | Confirmado en H69-H72: siempre se exige el tramo posterior a la publicación |
| Umbral t ≥ 3 para "descubrimientos" nuevos por minería de datos **[E]** | Harvey, Liu & Zhu, RFS 2016 | Las hipótesis **propias** (no reproducciones) necesitarán t ≥ 3 |
| Deflated Sharpe Ratio **[E]** | Bailey & López de Prado 2014 | En uso desde H69 |
| Probabilidad de sobreajuste (PBO) con CSCV **[E]** | Bailey, Borwein, López de Prado & Zhu, J. Comput. Finance | Obligatorio cuando una hipótesis propia tenga parámetros que elegir |
| Costes ≤ 1/3 del Sharpe bruto estimado de forma conservadora; Sharpe realista rara vez > 1 **[S]** | Carver, *Systematic Trading* (vía reseña de CXO Advisory) | **Nueva puerta previa**: estimar el coste por operación frente a la ventaja bruta antes de programar |
| Tasas reales de fondeo: 16,8% de Combines superados en 2025 y 33,3% de financiados cobraron (Topstep, disclosure oficial **[S]**); 14% aprueban y 7% cobran (FPFX, >300.000 cuentas, 2024) **[S]** | Topstep; Finance Magnates/FPFX | La probabilidad simulada de una estrategia debe superar claramente la tasa base, que corresponde a operar sin ventaja |

## 3. Lecciones propias (de 93 ensayos)
1. **Coste frente a ventaja decide casi todo.** H74 tiene un Sharpe bruto de 1,23 dentro de muestra,
   pero su punto de equilibrio (0,025 $/acción) es justo el coste de un CFD del US500. En futuros
   sobrevive parcialmente.
2. **Los artefactos de datos fabrican ventajas.** Huso horario de HistData (H69), BID deprimido en el
   rollover (H73), duplicados en Kaggle (H74). Regla: comprobar BID/ASK en los momentos de
   ejecución y la zona horaria con un evento conocido.
3. **El fondeo penaliza la cola izquierda diaria, no la media.** Las estrategias de "comprar caídas"
   concentran su exposición en los días de pánico y rompen la pérdida diaria aunque ganen a largo
   plazo (H75).
4. **Benchmark con la misma exposición.** Varias estrategias de Connors parecen buenas (PF 2, 77%
   ganadoras), pero no superan a entradas aleatorias con la misma duración y el mismo filtro de
   tendencia: es beta de tendencia alcista.
5. **Los estilos macro publicados no tienen ventaja reciente (dato independiente de AQR).** En
   *Century of Factor Premia* (AQR, mensual, hasta feb-2026; `research/fase71/aqr_cribado.py`), value,
   momentum y carry en índices, divisas, materias primas y bonos tienen Sharpe bruto 2012-2026 entre
   −0,6 y +0,45, y ninguno llega a t = 2. Solo sobreviven la selección de acciones (multi-estilo
   internacional SR 1,96, defensivo) y la prima de mercado de renta variable (SR 0,90), que no se pueden
   operar como ventaja en una cuenta de fondeo CFD. Coincide con H70 (trend following POST SR ≈ 0).
   Consecuencia: no volver a probar estilos macro lentos; buscar en horizontes intradía y microestructura.
6. **Las anomalías decaen tras publicarse, pero no siempre a cero.** H77 (oro en Tokio) desaparece
   (OOS t = 0,2); H78 (BTC 21-23 UTC) se mantiene en bruto (t = 3,0) pero baja de 12 a 5 pb, por debajo
   del coste de un CFD. La pregunta decisiva es el coste por operación en la cuenta concreta.

## 4. Cambios de metodología que se aplican desde ahora
1. **Puerta de costes** antes de programar: ventaja bruta esperada por operación ≥ 3 × coste realista
   del instrumento y la cuenta donde se operaría.
2. **Puerta de viabilidad de fondeo:** volatilidad diaria tras dimensionar ≤ 1%; percentil 1 del P&L
   diario por encima de −2,5% del capital; ninguna posición abierta en el rollover; definir si cruza
   fines de semana.
3. **Dimensionamiento por volatilidad** como norma en todo diseño propio orientado a fondeo.
4. **Hipótesis propias:** t ≥ 3 y PBO < 0,2 si hay parámetros; reproducciones fieles: t ≥ 2 OOS + DSR.
5. **Comparar con la tasa base** de las prop firms en todas las simulaciones de fondeo.

## 5. Hipótesis propias (pendientes de pre-registro, por orden de prioridad)
| Id | Hipótesis | Mecanismo | Por qué encaja en fondeo |
|---|---|---|---|
| P1 | RSI(2)<5 de Connors con tamaño inversamente proporcional a la volatilidad (2%/σ diaria, como ZAB) y límite interno diario | Reversión tras ventas forzadas / provisión de liquidez | Mantiene la ventaja OOS de H75f y estabiliza el riesgo diario, que es lo que hacía fallar el fondeo |
| P2 | Noise Area (H74) con costes de micro-futuros (MES) y fuera de muestra 2021-2026 | Coberturas gamma / desequilibrios intradía | Cierra cada día: sin gaps ni swaps. Requiere prop firm de futuros que permita bots |
| P3 | Cartera de ventajas débiles no correlacionadas (P1 + P2 + componente de calendario de fin de mes de H72) | Diversificación: la volatilidad diaria baja más que la media | Más días con ganancias pequeñas y menos días extremos: mejor para consistencia y límite diario |
