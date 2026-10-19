# Pre-registro H74 — Intraday momentum SPY "Noise Area" (Zarattini, Aziz & Barbon 2024)

Redactado y enviado a git ANTES de cargar los datos de SPY y de calcular ningún resultado.

## 1. Fuente
Zarattini, Aziz & Barbon, *Beat the Market: An Effective Intraday Momentum Strategy for S&P500
ETF (SPY)*, SFI Research Paper 24-97; versión del 3-feb-2025 leída completa (repositorio de la
Universidad de St. Gallen). Muestra del paper: 2007 → abril-2024. Resultado de la versión final
(banda actual + VWAP, tamaño dinámico): 19,6% anual neto, Sharpe 1,33, MDD 25%, 7.668 operaciones,
hit ratio 37% por operación / 43% por día. Tabla de rentabilidades mensuales 2007 → enero-2025 en
el FAQ (Q24); los meses posteriores a la publicación (mayo-2024 en adelante) son **autodeclarados por
los autores**, no una verificación independiente. Con su modelo de deslizamiento alternativo
(Kissell) el Sharpe baja a 1,17.

Réplicas encontradas: indicador "Concretum Bands" en TradingView y un backtest en QuantConnect
(sin estadísticas fuera de muestra). Ninguna verificación independiente de rentabilidad.

## 2. Reglas (literales del paper; no se elimina ningún componente)
- Día t, sesión regular 9:30-16:00 ET. Open_t = apertura de la vela de 9:30.
- move_{t−i,HH:MM} = |Close_{t−i,HH:MM} / Open_{t−i,9:30} − 1|, i = 1..14;
  σ_{t,HH:MM} = media de los 14 días anteriores (por minuto del día).
- UpperBound = max(Open_t, Close_{t−1,16:00}) × (1 + σ); LowerBound = min(Open_t, Close_{t−1,16:00}) × (1 − σ).
- Decisiones **solo a HH:00 y HH:30**, de 10:00 a 15:30. Precio de decisión = cierre del minuto
  que termina en HH:MM. Ejecución en la apertura del minuto HH:MM.
- Sin posición: largo si precio > UpperBound; corto si precio < LowerBound.
- Con posición larga: se cierra si precio < max(UpperBound, VWAP); si además precio < LowerBound,
  se abre corto (giro). Simétrico para cortos con min(LowerBound, VWAP).
- VWAP de la sesión regular desde 9:30, con el volumen de cada vela y su precio medio ("average" de
  Interactive Brokers en los datos).
- Cierre obligatorio a las 16:00 (cierre de la última vela).
- Tamaño: acciones = floor(AUM_{t−1} × min(4, 2% / σ_SPY,t) / Open_t), con σ_SPY,t = desviación
  típica (n−1) de los 14 últimos rendimientos diarios cierre-cierre. Capital inicial 100.000 $.
- Costes del paper: 0,0035 $/acción de comisión + 0,001 $/acción de deslizamiento por lado.

**Ambigüedades declaradas (interpretación fijada ahora):** (a) tras un stop, se permite reentrar más
tarde el mismo día si vuelve a cumplirse la condición (coherente con 1,8 operaciones/día); (b) la
regla de giro se evalúa en el mismo instante que el stop; (c) los primeros 14 días hábiles de
datos sirven de calentamiento y no operan.

## 3. Datos
- Muestra original: SPY 1 minuto con volumen, 2008-01-22 → 2021-05-06 (Kaggle
  `rockinbrock/spy-1-minute-data`; formato de Interactive Brokers con barCount y average). Hora
  original en Mountain Time (7:30 = 9:30 ET): se verificará contra los cierres diarios de Yahoo
  antes de usarla. Segundo fichero de Kaggle (`gratefuldata/...`) para contrastar.
- `calidad_datos.auditar_historico()` sobre las barras diarias RTH; los días con menos de 380
  minutos de sesión o en huecos GRAVES se excluyen (no se rellena nada).
- **Fuera de muestra (jun-2021 → oct-2026): pendiente de datos con volumen** (Alpaca, datos SIP
  gratuitos, requiere que el usuario cree una clave). Sin VWAP la estrategia no es reproducible
  fielmente, así que no se sustituirá por una aproximación.

## 4. Evaluación y criterios
1. **Fidelidad:** correlación de las rentabilidades mensuales de la reproducción con la tabla del
   paper (2008-02 → 2021-04) ≥ 0,7, y Sharpe de la reproducción con costes del paper ≥ 1,0.
   Si no se alcanza, se investiga la diferencia antes de cualquier conclusión.
2. **Costes de CFD/fondeo** (US500 de una prop firm): spread de 0,4-0,6 pt del índice
   (≈0,04-0,06 $ por acción equivalente de SPY) por ida y vuelta + comisión; se informa el
   coste de equilibrio.
3. **Fuera de muestra** (cuando haya datos): Sharpe neto > 0 con t ≥ 2 en jun-2021 → oct-2026.
4. **Fondeo:** simulación con `research/fondeo/simulador_fondeo.py` (FTMO 2-Step, FundedNext,
   Topstep) a distintos tamaños de riesgo, con el P&L diario y el mínimo intradía reales.
5. Dos motores independientes idénticos. N de ensayos acumulado: 82.
