# C116 — Resultados: mejoras de la cartera CFD (Upcomers)

Preregistro: `PREREGISTRO_C116_mejoras_cartera_cfd.md` (subido antes de calcular). Script: `c116_mejoras_cartera_cfd.py`; salida: `c116_resultados.txt`.
Base: cartera CFD con costes de Upcomers (con diarias), 2018-03-26 → 2026-09-30, control de volatilidad. Sharpe 1,82 (2018-21 1,33; 2022-26 2,25).

| Candidata | ΔSharpe (total / 18-21 / 22-26) | Neta por operación | Resultado |
|---|---|---|---|
| K1 bitcoin 21-23 UTC, 1,2 pb, peso 0,2 | +0,26 / +0,41 / +0,11 | +6,53 pb (t 3,55) | **PASA** |
| K2 euro E2, 0,95 pb | −0,47 / −0,28 / −0,65 | +0,46 pb (t 1,54) | NO PASA (informativo con 0,52 pb: ΔSharpe −0,05) |
| K3 C113 oro Asia, 1,36 pb, peso 0,2 | +0,09 / −0,03 / +0,19 | +1,71 pb (t 1,42) | NO PASA |
| K4 oro viernes salida 16:55 | +0,17 / +0,07 / +0,24 | tramo 16:45-16:55 +0,93 pb (t 3,57) | **PASA** |

**Cartera con K1 + K4: Sharpe 2,24 (2018-21 1,80; 2022-26 2,60).**
- Riesgo 0,5 %: 13,8 %/año (al 60 % ≈ 8,3 %), caída máx. −6,0 % (base: 11,0 %, −9,0 %).
- Riesgo 0,65 %: 18,0 %/año (al 60 % ≈ 10,8 %), caída máx. −7,8 % (base: 14,2 %, −11,7 %).

Cambios en el EA: E8 sale a las 16:55 (por defecto); bitcoin sigue activo; C113 y euro siguen desactivados.

Límites:
- Bitcoin: la ventaja ha bajado desde que se publicó (de 12 a 5 pb brutos); la mejora en 2022-26 (+0,11) es menor que en 2018-21. Serie de Binance (contado), no del CFD de Upcomers.
- K4: el oro de Upcomers cotiza hasta las 16:59 según solo 2 viernes medidos; si deja de cotizar antes, el EA sale antes de la pausa de sesión.
- Los costes de comisión suponen 5 $/lote por lado (no confirmado si es ida y vuelta: entonces serían menores).
- Todo es backtest; «al 60 %» es el escenario prudente habitual, no una medida.
