# Pre-registro C22 — Efecto de horario local en CZK, SGD y NZD (21-oct-2026)

Redactado y enviado a git ANTES de descargar USDCZK/USDSGD y de calcular ningún resultado (NZDUSD ya estaba descargado
para B1, que lo miró solo en franjas de 1-2 h en hora de NY, no en su sesión local completa).

## Pruebas (3; Holm)
- **USDCZK**, sesión europea 07:00 Londres → 08:00 NY (igual que C20). Unilateral: rentabilidad > 0 (corona débil en su horario).
- **USDSGD**, sesión de Singapur 09:00 → 17:00 hora de Singapur. **Bilateral**: el estudio original predice SGD débil
  (USDSGD > 0), pero en Asia el signo se invirtió en el yen y el AUD (C5); se acepta cualquier signo.
- **NZDUSD**, sesión de Wellington 09:00 → 17:00 hora de Nueva Zelanda (con su horario de verano). **Bilateral.**

## Datos, tramos y criterios
HistData M1 BID (hora de NY con horario de verano), 2010 → 2026-09; mismo cálculo de precios que C3/C20. Ningún extremo
cae en el rollover de las 17:00 NY (Singapur 09:00 = 20:00/21:00 NY del día anterior; Wellington 09:00 ≈ 16:00-17:00 NY:
**se comprueba y, si cae a menos de 30 min del rollover, se usa 10:00 Wellington** — decisión fijada aquí).
Descubrimiento 2010-2017: signo de la media (para las bilaterales fija el sentido). Confirmación 2018 → 2026-09: mismo signo
con t de Newey-West ≥ 2,39 (Holm para 3) y ≥ 60% de años con ese signo. Informativo: resto del día y correlación con E1.
Costes: hay que medirlos antes de operar (spreads de referencia: CZK 5, SGD 2, NZD 1,5 pb). Contador +3 (N ≈ 1.181).
