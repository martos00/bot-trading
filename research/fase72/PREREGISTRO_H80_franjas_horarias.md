# Pre-registro H80 — Barrido de franjas horarias intradía con descubrimiento y confirmación separados

Redactado y enviado a git ANTES de calcular ningún resultado (20-oct-2026).

## Motivación
La única anomalía de este proyecto que sobrevivió fuera de muestra (H78, BTC 21-23 UTC, t = 3,0 tras su publicación)
es una franja horaria. Estacionalidades intradía ligadas a horarios institucionales (aperturas, cierres, fixings,
coberturas) tienen un mecanismo plausible (flujos predecibles, inventario de intermediarios) y se pueden operar con
operaciones cortas sin swap. H80 busca de forma sistemática en mercados con datos ya auditados, con un diseño que
impide que el descubrimiento valide sus propios resultados. No se repiten franjas ya descartadas como hipótesis
individuales (overnight drift 2-3 a.m. ET, fixings FX, USDJPY-Tokio, oro-Tokio): entran en el barrido como una
franja más, sin trato especial.

## Universo y datos
HistData M1 (BID), zona horaria de Nueva York con horario de verano (verificada en H69/H71/H77):
SPXUSD, NSXUSD (2010-2026), XAUUSD, EURUSD, GBPUSD, USDJPY (se usa 2010-2026 en todos). `calidad_datos` sobre barras
diarias de cada instrumento; los días dentro de huecos (± 1 día) se excluyen.

## Franjas (fijadas, sin parámetros que ajustar)
- Inicio en cada hora en punto de Nueva York (0-23) y duración de **1 h y 2 h**: 48 franjas por instrumento,
  **288 en total**.
- Rentabilidad = log(precio al final / precio al inicio), con el cierre del último minuto ≤ hora (tolerancia 5 min).
- Solo días de inicio lunes-viernes. Se excluye toda franja que toque **17:00-18:00 ET** (pausa diaria, rollover y
  artefacto del BID detectado en H73).
- Dirección: la del signo de la media en el tramo de descubrimiento (largo si > 0, corto si < 0).

## Tramos
- **Descubrimiento: 2010-01-01 → 2017-12-31.** Pasa a confirmación toda franja con |t de Newey-West (5 rezagos)| ≥ 3,0.
- **Confirmación: 2018-01-01 → 2026-09-30.** Solo se evalúan las franjas que pasaron el descubrimiento.

## Costes por operación ida y vuelta (caso base; estrés = ×2)
Índices con costes de micro-futuros (cuenta de fondeo de futuros): SPX 1,5 pb, NSX 1,0 pb.
CFD (cuenta de fondeo CFD): XAUUSD 1,5 pb, EURUSD 1,0 pb, GBPUSD 1,2 pb, USDJPY 1,0 pb.
Simplificación declarada: el spread real depende de la hora; si una franja se confirma, antes de darla por buena se mide
el spread a esa hora con ticks (como en H71/H73).

## Criterio de confirmación (todos a la vez)
1. Mismo signo que en el descubrimiento y t ≥ t_Bonferroni en confirmación, bruto: t unilateral con p < 0,05 / k,
   donde k = número de franjas que pasaron el descubrimiento.
2. Neto del caso base: media > 0 con t ≥ 2,0.
3. Puerta de costes: media bruta ≥ 3 × coste base.
4. Positiva en ≥ 6 de los 9 años de confirmación (2018-2026).
5. Motor independiente (Python puro sobre los CSV) reproduce la media de las franjas confirmadas.
Lo que cumpla todo pasa a medición de spreads a esa hora y a simulación de fondeo. N acumulado: 94 + 288 = **382**.
