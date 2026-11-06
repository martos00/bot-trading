# PREREGISTRO C112 — Momentum entre sesiones en oro y plata: largo en la sesión asiática — 06-nov-2026

Redactado y subido a git ANTES de calcular. Inspiración: Wei (2026), «Who Moves the Price? Trading-Session Return Decomposition and
Cross-Session Momentum in Gold and Silver Markets», SSRN 7257240 (agosto de 2026). NO he podido leer el artículo (SSRN devuelve 403);
solo el resumen de un buscador: la sesión asiática acumula la mayor parte de la rentabilidad del oro y la plata, hay momentum de corto plazo
que se traslada a esa sesión, y una versión solo larga tiene Sharpe neto 1,68 (oro) y 0,84 (plata). Las reglas de abajo son MÍAS, no las
del artículo.

## Reglas (hora de Nueva York)
Sesiones: Asia 18:00 → 03:00; día anterior completo = 18:00 → 17:00 del día anterior.
- P (principal, oro): largo de 18:00 a 03:00 si la rentabilidad del día anterior completo fue > 0; si no, fuera. Solo largo.
- S (plata): la misma regla en plata.
- Controles (no deciden): largo en Asia todos los días (sin señal); largo en Asia cuando el día anterior fue < 0.
Opera de domingo a jueves por la tarde (la sesión de Asia del lunes empieza el domingo a las 18:00). Cabe en cuentas que cierran a las 16:59
(se abre a las 18:00 y se cierra a las 03:00, dentro de la misma sesión del CME).

## Datos, costes y criterio
Principal: HistData 1 min (XAUUSD, XAGUSD) 2010-06 → 2026-09. Confirmación: Databento 1 h de GC y SI (frontal; cambios de contrato
excluidos). Costes: oro 0,74 pb, plata 2,3 pb.
Pasa (Bonferroni 2 pruebas → t ≥ 2,24) si en la principal: media neta > 0 con t (Newey-West) ≥ 2,24; > 0 en 2010-17 y en 2018-26;
≥ 60 % de años positivos; > 0 desde 2023; y la confirmación con futuros tiene media neta > 0 con t ≥ 2,0. Además, para entrar en la cartera
debe superar al control «largo en Asia todos los días» (que la señal aporte algo) y no estar correlacionada > 0,5 con C99. Contador +2.
