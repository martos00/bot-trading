# Resultados C23 — Cruces EUR/PLN-HUF-CZK y vuelta del dólar por la tarde: PASAN EN BID, PENDIENTE DE VERIFICAR ARTEFACTO

Pre-registro `PREREGISTRO_C23_cruces_y_tarde.md`; script `c23_cruces_y_tarde.py`; salidas `c23_resultados.txt`, `c23_cartera.txt`.

| Prueba | 2010-2017 | 2018-2026 | Holm |
|---|---|---|---|
| EURPLN 07 Londres→08 NY (+) | +2,7 pb (t 3,86) | +2,0 pb (t 3,65), 100% años | Sí |
| EURHUF (+) | +1,5 pb (t 1,87) | +3,8 pb (t 2,21), 67% | Sí |
| EURCZK (+) | +1,6 pb (t 2,91) | +1,6 pb (t 3,57), 100% | Sí |
| USDPLN 08→16 NY (−) | −3,7 pb (t −2,74) | −2,9 pb (t −3,12), 100% | Sí |
| USDHUF 08→16 NY (−) | −3,8 pb | −3,1 pb (t −2,83), 89% | Sí |
| USDCZK 08→16 NY (−) | −3,1 pb | −1,8 pb (t −2,16), 89% | Sí |

## ALERTA: posible artefacto del BID (no se certifica hasta verificarlo)
Los datos de HistData son solo BID. En divisas de Europa central el spread es mucho más ancho a las 07:00 de Londres y a las
16:00 de NY (fuera de su horario líquido) que a las 08:00 NY. Un spread ancho hunde el BID, y eso fabrica exactamente el
patrón observado: USD/xxx "sube" de 07:00 Londres a 08:00 NY y "baja" de 08:00 a 16:00 NY (y los cruces EUR/xxx "suben" por
la mañana). Es la misma trampa que H73 (yen en Tokio). Esto afecta también a C20 y C22 (USDPLN/HUF/CZK por la mañana).
Verificación en curso: muestra de Dukascopy con BID y ASK (primer día hábil de cada mes, 2025-01 → 2026-09, USDPLN y USDHUF)
para medir el spread a esas horas; artefacto esperado = (spread_inicio − spread_fin) / 2.
La simulación de cartera (`c23_cartera.txt`) daba ≈ 24% anual al 1% de riesgo con costes de 1 pb, pero NO es fiable hasta
descartar el artefacto.
