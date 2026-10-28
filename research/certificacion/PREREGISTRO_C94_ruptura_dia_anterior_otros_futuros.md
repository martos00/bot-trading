# PREREGISTRO C94 — Ruptura del máximo/mínimo de la sesión anterior (regla C93-B) en otros 9 futuros — 28-oct-2026

Redactado y subido a git ANTES de calcular. C93 (oro) pasó en dos fuentes. Si el mecanismo es general (órdenes stop acumuladas sobre el
máximo/mínimo de ayer → continuación), debería aparecer en otros mercados. Si aparece en varios, al ser operaciones diarias poco
correlacionadas subirían mucho el Sharpe de la cartera de futuros. Regla idéntica a C93 variante B, con la salida de las firmas de futuros:
- Sesión 17:00 → 17:00 NY; máximo/mínimo de la sesión anterior; ATR(14) de sesiones.
- Ventana 08:00 → 15:00 NY; primera ruptura del día; entrada al nivel (o a la apertura del minuto si abre más allá).
- Stop 1 × ATR, objetivo 3 × ATR, **cierre 16:45 NY**. Ruptura de ambos niveles en el mismo minuto: sin operación.

## Mercados (9 pruebas) y coste del futuro (pb, ida y vuelta, aprox. 1 tick + comisión)
Plata SI 2,3 · crudo CL 1,6 · euro 6E 0,6 · libra 6B 0,8 · yen 6J 0,8 · dólar australiano 6A 1,0 · dólar canadiense 6C 1,0 ·
franco 6S 1,0 · Nikkei NKD 1,5. Sin parámetros por mercado.

## Datos
- Principal: HistData M1 2010-06 → 2026-09 (XAGUSD, WTIUSD, EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, JPXJPY). En los pares
  con el dólar delante (USDJPY, USDCAD, USDCHF) el signo se invierte para expresarlo como el futuro (la regla es simétrica: no cambia nada).
- Confirmación: futuros Databento en barras de 1 h (2010 → 2026, contrato frontal; sesiones con cambio de contrato excluidas). Misma
  regla aproximada a barras horarias: barras de 08:00 a 14:00 NY, salida al cierre de la barra de las 15:00 (16:00 NY).

## Criterio por mercado (Bonferroni unilateral 0,05/9 → t ≥ 2,54)
HistData: media > 0 con t (Newey-West) ≥ 2,54; ≥ 60 % de años positivos; > 0 en 2010-19 y en 2020-26; media > coste.
Y confirmación en Databento: media > 0 con t ≥ 2,0 y media > coste. Pasa ambas → candidata para la cartera de futuros (forward).
Informativo: cesta de igual riesgo de los 9; largos/cortos. Contador +9.
