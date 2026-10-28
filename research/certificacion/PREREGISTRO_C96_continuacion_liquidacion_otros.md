# PREREGISTRO C96 — Continuación en la media hora previa a la liquidación en bonos, cereales y cobre (extensión de C95) — 28-oct-2026

Redactado y subido a git ANTES de calcular. C95: en energía la media hora previa a la liquidación continúa el movimiento del día (NG
lo mantiene tras 2018). Mecanismo general: fondos y ETF (apalancados en bonos: TMF/TMV ×3, TBT −2; índices de materias primas) ejecutan
contra la liquidación en el sentido del día. Se mide si existe en otros mercados del CME con hora de liquidación conocida.

## Regla (hora de NY), idéntica a C95
r = ln(P(L − 30 min) hoy / P(L) sesión anterior); posición en el sentido de r de L − 30 min a L (salida a la liquidación).
| Futuro | Liquidación L | Ventana | Coste (pb, aprox.) |
|---|---|---|---|
| ZB bono 30 años | 15:00 | 14:30-15:00 | 3,0 |
| ZN bono 10 años | 15:00 | 14:30-15:00 | 1,8 |
| ZC maíz | 14:15 | 13:45-14:15 | 3,0 |
| ZS soja | 14:15 | 13:45-14:15 | 2,5 |
| ZW trigo | 14:15 | 13:45-14:15 | 3,5 |
| HG cobre | 13:00 | 12:30-13:00 | 2,0 |
6 pruebas. Datos: QuantConnect 1 min 2010-06 → 2026-09, desfase horario calibrado en B22 (+1 h en ZB, ZN, ZC, ZS, ZW; 0 en HG).
Placebo informativo: la media hora anterior. Sin segunda fuente a 1 minuto: lo que pase queda como candidata.

## Criterio (Bonferroni unilateral 0,05/6 → t ≥ 2,64)
Descubrimiento 2010-06 → 2017: media > 0. Confirmación 2018 → 2026-09: media > 0 con t (Newey-West) ≥ 2,64, ≥ 60 % de años positivos
y media > coste. Contador +6.
