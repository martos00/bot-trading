# H80 — Barrido de franjas horarias: RESULTADOS (20-oct-2026)

Pre-registro: `PREREGISTRO_H80_franjas_horarias.md` (commit d80cca7, antes de calcular). Salida: `h80_resultados.txt`.
Motores: `h80_motor.py`, `h80_evaluacion.py`. Datos HistData M1 2010-2026; auditoría VÁLIDA en FX y oro; en SPX/NSX el
hueco de feb-2017 se excluye (± 1 día).

**Desviación declarada:** la exclusión de 17:00-18:00 ET deja **45 franjas por instrumento (270)**, no 48 (288) como
decía el pre-registro por un error de cuenta. La regla no cambia. N acumulado = 94 + 270 = **364**.

## Descubrimiento 2010-2017
Hay estructura real: |t| ≥ 3 en **24 de 270** franjas (por azar se esperarían ≈ 0,7) y |t| ≥ 2 en 62 (≈ 12 por azar).

## Confirmación 2018-2026 (k = 24, t de Bonferroni unilateral = 2,87)
Solo **2** de las 24 mantienen la señal bruta con significación de Bonferroni; **ninguna cumple todos los criterios**:

| Franja | Lado | Bruto conf. | t conf. | Neto base | t neto | Años + | Por qué no se confirma |
|---|---|---|---|---|---|---|---|
| GBPUSD 16:00-17:00 ET | corto | 1,69 pb | 12,51 | +0,49 pb | 3,62 | 9/9 | **Artefacto**: 1,50 de los 1,69 pb ocurren entre 16:55 y 17:00 (t = 22), cuando el spread se ensancha y el BID cae antes de la pausa (igual que en H73). En 16:00-16:55: 0,17 pb, t = 1,4. No es operable. Además no pasa la puerta de costes |
| EURUSD 06:00-08:00 ET | corto | 1,48 pb | 4,85 | +0,48 pb | 1,57 | 8/9 | Real pero pequeña: neto t = 1,57 < 2 y 1,48 pb < 3 × coste (3,0 pb) |

Las otras 22 franjas pierden la significación o cambian de signo: entre ellas las del Nasdaq/S&P de 1-3 a.m. ET (la
"overnight drift" ya descartada por sus autores: +0,4 a +1,3 pb, t ≤ 2,2) y las de oro, que decaen a ~0. (Comprobación
del artefacto: EURUSD 16:55-17:00 da 0,92 pb con t = 20, el mismo fenómeno.)

## Veredicto: ninguna franja candidata
Existe estacionalidad intradía en el descubrimiento, pero lo que sobrevive en confirmación es o un artefacto del BID
antes del rollover o efectos de 1-2 pb, por debajo de lo necesario para cubrir costes con margen. Coincide con la
lección del proyecto: en mercados líquidos las ventajas horarias reales existen pero son menores que el coste de
ejecución de una cuenta retail o de fondeo.
