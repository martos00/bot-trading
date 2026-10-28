# PREREGISTRO C88 y C89 — Régimen de gamma de los creadores de mercado (opciones) y dirección intradía — 28-oct-2026

Redactado y subido a git ANTES de calcular. Mecanismo común: si los creadores de mercado tienen gamma NEGATIVA, su cobertura compra cuando
sube y vende cuando baja (amplifica → continuación); con gamma POSITIVA hacen lo contrario (frena → reversión). Antecedente: C11 (S&P,
GEX de SqueezeMetrics, última media hora): signo correcto pero no significativo. Aquí con datos propios de opciones de QuantConnect.
Convención (SqueezeMetrics): creadores de mercado largos en calls y cortos en puts → GEX = Σ OI × gamma × S² × 0,01 × (+1 call, −1 put).

## C88 — Oro (futuro GC y opciones OG), cada día laborable
- 09:31 NY: GEX con las opciones de vencimiento ≤ 60 días y strikes a ±10 % del subyacente (interés abierto del día; gamma de
  QuantConnect). Señal de precio: s = signo del movimiento desde el cierre de las 13:30 del día hábil anterior hasta las 09:31.
- Regla: si GEX < 0, posición en el sentido de s; si GEX > 0, en sentido contrario. De 09:31 a 13:30 NY.
- Control informativo: la misma posición sin condicionar (siempre en el sentido de s).

## C89 — S&P 500 (futuro ES) en días de vencimiento de opciones semanales/diarias del índice (SPXW)
- Días con vencimiento SPXW ese mismo día (0DTE). 15:00 NY: GEX de las SPXW que vencen hoy, strikes a ±3 % del índice.
- Señal: s = signo del ES de 09:30 a 15:00. Si GEX < 0 → sentido de s; si GEX > 0 → contrario. ES de 15:00 a 16:00 NY.
- Si QuantConnect no tiene SPXW o no hay datos suficientes (< 300 días), la prueba se declara no realizable (no se sustituye por otra).

## Criterio (2 pruebas)
Media > 0 con t (Newey-West) ≥ 2,24; > 0 en las dos mitades (C88: ≤ 2018 / ≥ 2019; C89: mitad de los días disponibles); media de la
segunda mitad > coste del futuro (GC 0,74 pb; ES 0,73 pb); y mejor que el control sin condicionar. Contador +2.

## Anexo (antes de calcular; motivo técnico)
Con opciones a 1 minuto, C88 tardaría ~7 h en QuantConnect gratis. Se usan opciones con resolución horaria: la gamma y la señal se
calculan a las **10:00 NY** (no 09:31) y la posición va de 10:00 a 13:30. Señal s = signo de 13:30 del día anterior → 10:00. Resto igual.
Solo se ha visto marzo de 2022 como prueba técnica de funcionamiento (GEX positiva todo el mes).
