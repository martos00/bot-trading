# Pre-registro H70 — Trend following diversificado (Hurst, Ooi & Pedersen 2017)

Redactado y enviado a git ANTES de construir el panel de datos y de calcular ningún
resultado. Cambios posteriores solo como apéndices fechados.

## 1. Qué se reproduce

**Hurst, Ooi & Pedersen (2017)**, "A Century of Evidence on Trend-Following Investing",
*JPM* 44(1). Leído el PDF completo (aqr.com). Reglas: combinación equiponderada de
señales de momentum de serie temporal a **1, 3 y 12 meses** (signo del exceso de
rentabilidad pasado: largo si > 0, corto si < 0, siempre posicionado); cada posición
dimensionada para igual volatilidad; cartera escalada a **10% de volatilidad anual
ex-ante**; rebalanceo mensual. 67 mercados (11 índices, 15 bonos, 10 divisas, 29 materias
primas), 1880-2016. Costes por clase de activo (tabla del paper, en imagen, no extraíble)
y comisiones 2/20.

Validación del motor (no es hipótesis): versión **Moskowitz-Ooi-Pedersen (2012)** — señal
12 meses, cada activo a 40% de vol ex-ante, media simple de los activos — comparada con
el factor oficial **AQR TSMOM** mensual (1985-2026, descargado de aqr.com).

## 2. Por qué no es una repetición de lo ya descartado

TSMOM anterior (`estrategia_tsmom.py`): 9 CFD (6 FX + oro + 2 índices EE.UU.), 3,75 años,
sin bonos ni materias primas, con el hueco de 2025. Turtle / Golden Cross: reglas de
ruptura/cruce sobre 3 mercados. Aquí: 34 mercados de 4 clases, hasta 50 años de historia,
fuentes oficiales (bancos centrales, FRED, Yahoo), y validación contra la serie publicada
por el propio autor.

## 3. Universo y datos (fijados de antemano)

Precios de **cierre** (último dato del mes; si el último dato tiene más de 5 días hábiles
de antigüedad, ese mes es NaN). **No se usan series de medias mensuales** (OCDE, FMI)
como precios, porque promediar induce autocorrelación positiva artificial que infla
cualquier estrategia de tendencia; sí se usan tipos cortos mensuales para el devengo.

| Clase | Mercados (fuente) | Exceso de rentabilidad mensual |
|---|---|---|
| Índices (11) | S&P 500, Russell 2000, Nikkei 225, DAX, FTSE 100, S&P/TSX, S&P/ASX 200, CAC 40, AEX, IBEX 35, FTSE MIB (Yahoo) | precio_t/precio_t-1 − 1 − tipo corto local/12 (dividendos omitidos salvo DAX, que es de rendimiento total: sesgo conservador declarado) |
| Bonos (9) | EE.UU. 2/5/10/30 (FRED), Alemania 10 (Bundesbank), R.U. 10 (BoE), Japón 10 (MOF), Canadá 10 (BoC), Australia 10 (RBA) | bono a la par comprado con cupón = rendimiento del mes anterior, revalorizado al rendimiento actual con vencimiento −1/12; menos tipo corto local |
| Divisas (9) | EUR (DEM antes de 1999, Bundesbank), JPY, GBP, CAD, CHF, AUD, NZD, SEK, NOK frente a USD (FRED H.10) | variación spot + (tipo extranjero − tipo USD)/12; desde marzo-1973 |
| Materias primas (5) | WTI, gas natural Henry Hub (FRED, contado), oro, plata, cobre (Yahoo, futuro continuo) | variación de precio (sin rendimiento de roll: limitación declarada; Lempérière et al. miden correlación 0,65 entre tendencia en contado y en futuros para materias primas) |

Tipos cortos: 3 meses interbancario OCDE vía FRED por divisa (empalmes: DEM→EUR en 1999;
JPY: tipo de descuento antes de 1985-07, call rate después; CHF: call rate hasta su último
dato, luego 3 meses).

Antes de calcular nada: `calidad_datos.auditar_historico()` sobre cada serie diaria de
precios; huecos GRAVES se reportan y los meses afectados quedan NaN.

## 4. Reglas H70 (sin parámetros libres adicionales)

- Volatilidad ex-ante por mercado: EWMA de rentabilidades mensuales al cuadrado con centro
  de masa 6 meses; un mercado entra cuando tiene ≥ 24 meses de historia.
- Señal por mercado: s = (sign(r_1m) + sign(r_3m) + sign(r_12m)) / 3, con r_k = exceso
  acumulado de los últimos k meses (hasta el cierre del mes t).
- Peso bruto: w_i = s_i / σ_i. Escalado de cartera a 10% anual ex-ante: la volatilidad de
  la cartera se estima aplicando los pesos actuales a los últimos 36 meses de
  rentabilidades (mínimo 24 con datos).
- La posición decidida al cierre del mes t se aplica al mes t+1.
- Resultado = rentabilidad de exceso (sobre el tipo corto) de la cartera.

## 5. Evaluación

- Períodos: **PRE** primer mes con ≥ 15 mercados → dic-2011 (anterior a la publicación de
  MOP 2012); **POST** ene-2012 → último mes disponible (la prueba que importa).
- Métricas: rentabilidad y vol anualizadas, Sharpe, t (Newey-West 3 rezagos), drawdown
  máximo, correlación con renta variable EE.UU., Sharpe por clase de activo y por señal.
- Benchmarks: AQR TSMOM en el mismo período; cartera "siempre larga" con los mismos pesos
  de riesgo (aísla la beta); signo aleatorio (5.000 simulaciones).
- Selección múltiple: DSR con N = 73.

## 6. Costes (estimaciones declaradas, a contrastar con el bróker real)

Coste por unidad de rotación de nocional (una vía) + coste anual sobre nocional bruto:

| Escenario | Índices | Bonos | Divisas | Materias primas |
|---|---|---|---|---|
| Futuros (micro/mini CME/Eurex) | 0,02% + 4 rolls/año | 0,02% + 4 rolls/año | 0,02% + 4 rolls/año | 0,04% + 6 rolls/año |
| CFD (spread + recargo de financiación sobre el tipo de referencia) | 0,01% + 2,5%/año | 0,02% + 2,5%/año | 0,01% + 1,0%/año | 0,03% + 2,5%/año |

(El tipo de referencia de la financiación del CFD ya está dentro del exceso de
rentabilidad; solo el recargo del bróker es coste adicional.)

## 7. Criterios de decisión

0. **Validación del motor:** correlación mensual de la versión MOP con AQR TSMOM
   1985-2026 ≥ 0,60. Si no se alcanza, H70 no se evalúa hasta corregir los datos
   (cada corrección se documenta).
1. Candidata con **futuros**: POST, Sharpe neto de costes de futuros > 0 con t ≥ 2,0 y
   DSR ≥ 0,95.
2. Candidata con **CFD**: lo mismo con costes CFD.
3. Si 1-2 fallan pero PRE es significativo: se reporta como "anomalía reproducible pero sin
   evidencia estadística suficiente después de su publicación", no como candidata.
