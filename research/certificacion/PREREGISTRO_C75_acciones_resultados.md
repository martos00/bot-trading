# PREREGISTRO C75 — Acciones de FTMO alrededor de la publicación de resultados — 26-oct-2026

Redactado y subido a git ANTES de calcular ninguna rentabilidad. Primer estudio con acciones individuales.

## Por qué (mecanismo de flujo)
- **Prima de anuncio de resultados** (Frazzini y Lamont 2007; Barber, De George, Lehavy y Trueman, JFE 2013): las
  acciones suben más de lo normal en los días en torno a la publicación de resultados programada. Explicación: compras
  por atención de inversores minoristas y demanda de cobertura antes del anuncio (flujo no informativo y predecible
  por calendario).
- **Deriva tras el anuncio (PEAD)** (Bernard y Thomas 1989): el precio sigue en la dirección de la reacción. Se sabe
  que en empresas grandes se ha debilitado mucho; se prueba como control de la familia.

## Datos (gratuitos, nada se compra)
- Universo: las 46 acciones de EE. UU. que FTMO ofrece como CFD (lista de `simbolos.csv` de la cuenta FTMO, oct-2026).
  Aviso de **sesgo de supervivencia**: la lista es de hoy (ganadoras como NVDA o PLTR). Por eso toda medida es
  **rentabilidad en exceso sobre el SPY y frente a los días sin resultados de la misma acción** (ver abajo).
- Precios: Yahoo Finance diarios (apertura y cierre ajustados por splits), 2012-01 a 2026-10. Mercado: SPY.
- Fechas de resultados: calendario de Nasdaq (api.nasdaq.com) por día, 2012-01-02 a 2026-10-23. Se aceptan los
  tickers antiguos FB→META, UTX/RTN→RTX.
- **Día de reacción R** (no se usa la hora que da Nasdaq, casi siempre "no disponible"): para una fecha de anuncio F,
  candidatos R = F (antes de la apertura) o R = siguiente día hábil (después del cierre). Se elige el de mayor
  |apertura/cierre anterior − 1| del valor en exceso sobre el SPY. Esto usa el tamaño del hueco, no su signo.
  Si F no es día de negociación o faltan precios, se descarta el evento.

## Reglas (3 pruebas, todas en rentabilidad del valor menos la del SPY en el mismo intervalo)
- **A1 — Subida previa (sin aguantar el anuncio)**: largo del cierre de R−2 al cierre de R−1. Se sale antes de la
  publicación, así que no hay hueco de resultados.
- **A2 — Prima con el anuncio**: largo del cierre de R−1 al cierre de R (incluye el hueco).
- **B — Deriva posterior**: dirección = signo del exceso de R−1 cierre → R cierre; posición en esa dirección del
  cierre de R al cierre de R+5.

## Costes supuestos (por operación, a verificar en la cuenta FTMO)
Ida y vuelta 6 pb + 2 pb por noche de financiación (A1 y A2: 1 noche; B: 5 noches + fin de semana ≈ 7 noches).

## Medida y criterio
- Para cada evento, exceso = rentabilidad del valor − SPY. Se compara con la media del mismo intervalo (misma longitud)
  en los días sin evento de la misma acción (±10 días hábiles alrededor de cada R excluidos), para quitar la deriva
  propia de ganadoras. Estadístico: media de (exceso del evento − media sin evento de esa acción), t con errores
  agrupados por fecha (los eventos del mismo día cuentan como uno).
- Descubrimiento 2012-2018, confirmación 2019-2026-10.
- **Pasa** si: en confirmación t ≥ 2,13 (unilateral 0,05/3) en la dirección prevista (positiva), media positiva en
  descubrimiento, y media neta de costes > 0 en confirmación. Lo que pase necesita segunda fuente de precios y medir
  costes reales en FTMO antes de pensar en operar. Lo que falle se cierra sin variantes. Contador +3.
