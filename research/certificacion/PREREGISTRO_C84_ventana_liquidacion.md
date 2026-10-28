# PREREGISTRO C84 — Presión en los minutos previos a la liquidación diaria (settlement) de futuros: oro, plata, S&P 500 — 28-oct-2026

Redactado y subido a git ANTES de calcular. Mecanismo candidato: fondos, coberturas y órdenes "trade at settlement" se ejecutan contra
el precio de liquidación, que el CME calcula con lo negociado en una ventana corta; los operadores que cubren esas órdenes pueden presionar
el precio en los minutos previos, más a fin de mes (rebalanceos). Ventanas de minutos: solo operables con costes de futuros. Nunca medido
(los barridos eran de 30-60 min).

## Datos y ventanas (hora de NY; futuros Databento 1 minuto, contrato del día; se descarta el día si cambia el contrato)
- Oro GC: 13:25 → 13:30 (liquidación 13:28-13:30). Plata SI: 13:20 → 13:25 (liquidación 13:23-13:25). S&P ES: 15:55 → 16:00
  (liquidación 15:59:30-16:00). Precio = cierre del último minuto anterior a cada hora.
## Tipos de día
(a) todos los laborables; (b) último día hábil del mes (D0, días con datos del propio mercado). 3 × 2 = 6 pruebas.
## Criterio (sin signo previsto)
Descubrimiento 2010-06 → 2017: |t (Newey-West)| ≥ 2,0 fija el signo (si no, se cierra). Confirmación 2018 → 2026-09 con ese signo:
t ≥ 2,39 (Bonferroni unilateral 0,05/6), ≥ 60 % de años con el signo y media ≥ 2 × coste del futuro (GC 0,74, SI 2,3, ES 0,73 pb).
Lo que pase necesita otra fuente y un plan de ejecución en una firma de futuros antes de nada. Contador +6.
