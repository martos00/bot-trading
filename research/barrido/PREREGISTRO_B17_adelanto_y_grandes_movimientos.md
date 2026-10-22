# Pre-registro B17 — Adelanto entre mercados (hora) y reacción tras días de movimiento extremo — 22-oct-2026
Redactado y enviado a git ANTES de calcular. Tipos de ventaja nuevos en el proyecto.
## (a) Adelanto entre mercados (lead-lag horario)
Mercados (h1 Databento, hora NY): ES, NQ, ZN, ZB, CL, GC, SI, HG, 6E, 6J, 6A, 6B. Para cada par ordenado (líder L, seguidor F), L ≠ F:
regla = signo(rentabilidad de L en la hora h−1) × rentabilidad de F en la hora h, todas las horas juntas (sin 16-18 NY), mismo día, sin cambio de
contrato. 132 reglas. Coste: el del seguidor (B2).
## (b) Día extremo
Mismos 12 mercados + 13 pares FXCM (cierres a las 16:00 NY). Evento: |rentabilidad diaria| > 2 × desviación de 60 días previa. Regla: posición al
día siguiente (cierre a cierre) a favor (momentum) o en contra (reversión): el signo lo fija el descubrimiento. 25 reglas. Coste: el de B2 o el real FXCM.
## Criterios
Descubrimiento 2010-06 – 2017 (FXCM 2012-2018); confirmación 2018 – 2026-09 (FXCM 2019-2026). Selección |t (NW)| ≥ 3,0 (pocas reglas); confirmación
t ≥ Bonferroni unilateral 0,05/k_sel (a y b por separado), ≥ 60 % de años, bruto ≥ 3 × coste. Contador +157.
