# Resultados C6 — Fixing de Londres de fin de mes (Melvin y Prins 2015): NO CERTIFICADA

Pre-registro: `PREREGISTRO_C6_fin_de_mes_fixing.md` (commit 40774db, antes de calcular). Script: `c6_fin_de_mes_fixing.py`.
Salida completa: `c6_resultados.txt`.

| | FXCM 2012-2026 (principal) | HistData 2003-2011 (confirmación) |
|---|---|---|
| Factor bruto (5 pares, media por mes) | 1,17 pb, t 0,86 (174 meses) | 2,98 pb, t 1,56 (108 meses) |
| Factor neto | 0,20 pb, t 0,15 | 2,03 pb, t 1,06 |
| Coste medio | 0,97 pb (bruto/coste 1,2) | 0,95 pb (mediana FXCM) |
| Años netos positivos | 8/15 | 5/9 |

Criterios: 1 ✗ (t neto 0,15 < 2), 2 ✗ (1,2× < 3×), 3 ✗ (53% < 60%), 4 ✗ (t 1,56 < 1,645). **Se descarta sin modificar la regla.**

Descriptivo (no era criterio): la reversión 16:00 → 17:00 Londres con signo contrario sale positiva en los dos períodos
(1,46 pb, t 2,44; 2,82 pb, t 2,63). No se usa para decidir: no estaba pre-registrada como prueba, ya se han visto los dos
períodos y su tamaño (1,5-3 pb) está por debajo de 3× el coste (≈ 1 pb). Solo podría estudiarse con datos futuros.
Contador de selección múltiple: +1 (N acumulado ≈ 1.155).
