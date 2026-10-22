# Pre-registro C63 — Confirmación de Brent/WTI (C62) con futuros, sin saltos de cambio de contrato — 22-oct-2026
Redactado y enviado a git ANTES de descargar BZ.
## Motivo
C62 certificó según sus criterios la reversión Brent/WTI con CFD de HistData (+114,6 pb/op, t 3,02), pero: (1) los CFD cambian de contrato en fechas
distintas (saltos artificiales en el diferencial); (2) 2020 (WTI negativo) aporta más de la mitad; (3) faltan operaciones en 2024-2025.
## Regla
Futuros diarios de Databento: BZ.c.0 (Brent, NYMEX) y CL.c.0 (WTI), cierre diario; rentabilidades diarias sin los días de cambio de contrato de cada
pata (se ponen a 0 ese día en el P&L y el diferencial se construye acumulando solo rentabilidades válidas, para que el z no vea saltos de contrato).
Misma regla de entrada/salida que C62 (z de 60 días, |z| > 2, salida al cambiar de signo o a 20 días); coste 8 pb + 0,5 pb/día.
## Criterios
2018 – 2026-09: media neta por operación > 0 con t (NW) ≥ 2,0 y ≥ 60 % de años positivos; y lo mismo **sin 2020**. Informativo 2010-2017 si hay
datos de BZ. Si no pasa, C62 queda como artefacto de los CFD. Contador +1.
