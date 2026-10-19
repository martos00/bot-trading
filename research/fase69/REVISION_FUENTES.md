# Fase 69 — Revisión documental de fuentes (octubre 2026)

## 1. Registro de acceso (qué se ha leído realmente)

| # | Fuente | Acceso | Qué se leyó |
|---|---|---|---|
| 1 | Lempérière, Deremble, Seager, Potters & Bouchaud (2014), *Two Centuries of Trend Following*, arXiv:1404.3274 | ✅ PDF completo | Texto íntegro (17 pp.) |
| 2 | Hurst, Ooi & Pedersen (2017), *A Century of Evidence on Trend-Following Investing*, JPM 44(1) | ✅ PDF completo (aqr.com) | Texto íntegro; las tablas (Exhibits) son imágenes y sus cifras **no** se pudieron extraer |
| 2b | AQR Data Set *Time Series Momentum: Factors, Monthly* (1985-2026) | ✅ xlsx | Serie completa, usada como benchmark independiente |
| 3 | Gao, Han, Li & Zhou (2018), *Market Intraday Momentum*, JFE 129(2) | ⚠️ SSRN bloqueado (403); leído el working paper de dic-2015 | Texto íntegro del WP (puede diferir en detalles de la versión publicada) |
| 3b | Baltussen, Da, Lammers & Martens (2021), *Hedging Demand and Market Intraday Momentum*, JFE 142 | ✅ PDF del autor (nd.edu) | Texto íntegro |
| 4 | Gatev, Goetzmann & Rouwenhorst (2006), *Pairs Trading*, RFS 19(3) | ⚠️ OUP de pago; leído el WP Yale ICF 08-03 (feb-2006) | Texto íntegro del WP |
| 5 | Bailey & López de Prado (2014), *The Deflated Sharpe Ratio*, JPM 40(5) | ⚠️ SSRN bloqueado; leído el PDF del autor (davidhbailey.com) | Texto íntegro y fórmula |
| 6 | Quantopian Lectures (community.quantopian.com) | ❌ La página solo devuelve el título (contenido cargado por JavaScript) | No leído |
| 7 | Hudson & Thames Research | ✅ índice de artículos (parcial, 100k de 228k caracteres) | Solo títulos/temas; ningún artículo leído entero |
| 8 | QuantConnect LEAN docs | No consultado en esta fase (herramienta, no fuente de evidencia) | — |
| 9 | VectorBT (GitHub) | Solo comprobado que es accesible (README) | — |
| 10 | Ernest Chan, *Optimizing Trading Strategies without Overfitting* (YouTube) | ❌ YouTube devuelve captcha desde esta sesión | No visto; no se cita su contenido |

Fuentes adicionales encontradas y leídas: Krohn, Mueller & Whelan (2024), JF 79(1) — WP Banco
de Canadá 2021-48, completo; Harvey, Mazzoleni & Melone (2025/2026), NBER WP 33554 — versión de
ene-2026, completa; McLean & Pontiff (2016), JF — **solo resumen** vía buscador (26% menos fuera
de muestra, 58% menos tras publicación); Boyarchenko, Larsen & Whelan (2023), RFS, *The
Overnight Drift* y su seguimiento en Liberty Street Economics (1-jul-2026) — **solo resumen**
vía buscador.

## 2. Fichas por estrategia

### A. Momentum intradía apertura/cierre (Gao et al. 2018; Baltussen et al. 2021)
- **Mercado/período:** SPY 1993-2013 (Gao); >60 futuros 1974-2020 (Baltussen).
- **Mecanismo:** rebalanceo tardío/informados (Gao); cobertura gamma de creadores de mercado de
  opciones y ETF apalancados (Baltussen).
- **Reglas:** signo de r(cierre anterior→10:00) o r(cierre anterior→15:30) → posición de
  15:30 a 16:00.
- **Resultados publicados:** R² 1,6%; 6,67%/año bruto (SR 1,08 sobre 30 min de exposición);
  4,46%/año tras spread 2001-2013. Baltussen no modela costes.
- **Costes considerados:** spread de SPY a las 15:30, salida en subasta de cierre (sin spread).
- **Datos:** M1 intradía con hora exacta.
- **Sesgos:** spread de SPY ≈1,2 pb no replicable en CFD (sin subasta de cierre).
- **Por qué dejaría de funcionar:** publicación; ventaja ≈ coste mínimo.
- **Equivalencia previa:** `hipotesis_momentum_intradia.py` NO era equivalente (sin tramo
  overnight, CFD 2023-2026, hora inferida).
- **Nuestra reproducción (H69): descartada** — se reproduce en 2010-2013 (+2,15 pb, t=2,06),
  desaparece tras 2020, coste del CFD > ventaja.

### B. Trend following diversificado (Lempérière et al. 2014; Hurst et al. 2017)
- **Mercado/período:** 27 futuros desde 1960 + contado desde 1800 (Lempérière); 67 mercados
  1880-2016 (Hurst).
- **Mecanismo:** infrarreacción/expectativas extrapolativas; intervención de bancos centrales;
  participantes que no buscan beneficio.
- **Reglas:** Lempérière: señal EMA normalizada (n≈5 meses), posición ±1/σ. Hurst: signo del
  exceso a 1, 3 y 12 meses, vol objetivo 10%, rebalanceo mensual.
- **Resultados publicados:** t≈5,9 desde 1960 (SR 0,8 sin costes), t≈10 desde 1800; Hurst:
  "consistentemente rentable" en cada década (cifras en imagen). Lempérière ya advertía que
  las tendencias cortas se han debilitado y que desde 2011 la estrategia estaba plana.
- **Costes:** Hurst: estimaciones propias por clase (×2 1993-2002, ×6 antes) y 2/20.
- **Datos:** precios de futuros de decenas de mercados.
- **Sesgos:** contado frente a futuros (correlación 0,65 en materias primas); supervivencia de
  mercados; en datos promediados mensualmente, autocorrelación artificial.
- **Post-publicación (AQR, 58 futuros):** SR bruto 1,41 en 1985-2009 frente a **0,38 en
  2012-2026 (t=1,46)**.
- **Equivalencia previa:** `estrategia_tsmom.py` (9 CFD, 3,75 años), Turtle y Golden Cross NO
  eran reproducciones fieles.
- **Nuestra reproducción (H70): no candidata** — motor validado (corr. 0,79 con AQR); SR 1,09 en
  1982-2011, −0,01 en 2012-2026; neto CFD −0,78.

### C. Pairs trading (Gatev, Goetzmann & Rouwenhorst 2006)
- **Mercado/período:** acciones CRSP 1962-2002.
- **Mecanismo:** reversión de mispricing temporal entre sustitutos cercanos; factor común
  "dormido".
- **Reglas:** formación 12 meses (distancia mínima entre precios normalizados), negociación 6
  meses, apertura a 2σ, cierre al cruce.
- **Resultados:** top-20 1,44%/mes (t=11,6) sobre capital empleado; 0,90% esperando un día;
  caída de 118 a 38 pb/mes en exceso bruto tras 1988 (ajustado por riesgo, de 67 a 42 pb).
- **Costes:** estimación de spread vía espera de 1 día; costes de préstamo para cortos.
- **Datos:** universo amplio de acciones con deslistadas (CRSP).
- **Sesgos:** supervivencia si se usan datos gratuitos sin deslistadas; selección de pares con
  información futura (ya ocurrió en `estrategia_pairs_trading_coint.py`).
- **Por qué dejaría de funcionar:** competencia de arbitrajistas (ya visible tras 1988).
- **Equivalencia previa:** USTEC-US500 y GBPUSD-USDCHF NO son equivalentes (2 pares frente a
  miles de acciones, cointegración frente a distancia).
- **Estado: no reproducido** — requiere un universo de acciones con deslistadas y CFD de
  acciones con corto disponible; los datos gratuitos (Yahoo) tienen sesgo de supervivencia.

### D. Otras anomalías con evidencia independiente
| Estrategia | Fuente | Estado |
|---|---|---|
| Reversiones en fixings FX | Krohn-Mueller-Whelan (JF 2024), G9 1999-2019 | **H71**: se reproduce (EUR Europa t=7,9) pero desaparece en 2020-2026; excepción pre-registrada **USDJPY-Tokio** (t=5,5 fuera de muestra) → validación H73 en curso |
| Front-running del rebalanceo 60/40 | Harvey-Mazzoleni-Melone (NBER 2025) | **H72**: se reproduce (SR 0,81 en su muestra); fuera de muestra (mar-2023→) SR 0,42 bruto, no significativo |
| Overnight drift (2-3 a.m. ET) | Boyarchenko-Larsen-Whelan (RFS 2023) | Descartada sin backtest: los propios autores informan (jul-2026) de que es ≈0 desde 2021 |
| Decaimiento general de anomalías | McLean-Pontiff (JF 2016) | Marco de interpretación: −26% fuera de muestra, −58% tras publicación |

## 3. Herramientas y método
- **DSR** (Bailey-López de Prado): aplicado en H69-H73 con N acumulado de ensayos.
- **VectorBT / LEAN:** no imprescindibles; el contraste entre motores se ha hecho con dos
  implementaciones propias independientes (vectorizada y bucle explícito) por hipótesis, con
  diferencia máxima ~1e-16.
- **Hallazgo de datos:** HistData (índices y FX) usa hora local de Nueva York **con** horario de
  verano, no "EST fijo" como dice su documentación.
