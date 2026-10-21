# Verificación con Databento (CME, contrato continuo por volumen) de C12, C16 y C15-N — reglas sin cambios

Script `v_databento_futuros.py`; salida `v_databento_resultados.txt`. Coste de los datos: ≈ 0,20 $ del crédito gratuito.
A diferencia de Yahoo, aquí se sabe qué contrato es cada barra y no se calcula ninguna rentabilidad entre contratos distintos.

| Prueba | Con Yahoo (antes) | Con Databento |
|---|---|---|
| C12 fin de mes, ZF 2019-2026 | +5,4 pb neto (t 2,86) | **+2,1 pb neto (t 0,89)** |
| C12 fin de mes, ZN 2019-2026 | +4,0 pb neto (t 1,35) | +0,5 pb neto (t 0,14) |
| C16 ventana FOMC, ZN 2020-2026 | +14,1 pb neto (t 1,09) | +11,0 pb neto (t 1,01) |
| C15-N gas, jueves 2017-2026 | −13,8 pb (t −0,81) | **−45,5 pb (t −2,94), 1/10 años positivo** |

- **Fin de mes en bonos:** con datos limpios casi desaparece; buena parte de lo que se veía con Yahoo venía de cambios de
  contrato mal filtrados (los vencimientos de bonos caen a fin de mes). Se retira de la lista de vigilancia.
- **Ventana FOMC:** se mantiene igual de débil (≈ 11 pb, t ≈ 1). Sigue en vigilancia.
- **Gas natural los jueves:** con las dos fuentes y en los dos períodos el jueves es **negativo** (lo contrario de lo que dice
  el estudio): 2010-2016 −32,8 pb (t −2,12), 2017-2026 −45,5 pb (t −2,94), frente a ≈ −3/−5 pb el resto de días. Como el
  sentido se descubrió al ver los datos, no se puede certificar con el pasado: **candidata nueva para vigilar hacia delante**
  ("corto en gas el jueves del informe"), pendiente de entender el mecanismo y de medir su coste en CFD.

## C9 (regla del 80% de Dalton) con el futuro ES de Databento (M1, sin días de cambio de contrato) — `v_databento_c9.py`
| | HistData SPXUSD (antes) | Databento ES |
|---|---|---|
| 2010-2017 | +1,5 pb (t 0,64) | +0,9 pb (t 0,53), 3/8 años |
| 2018-2026 | **+5,1 pb (t 2,54)**, 7/9 años | **+2,0 pb (t 0,81)**, 5/9 años |
Con el futuro real el resultado de 2018-2026 se reduce a menos de la mitad y deja de ser significativo. **No se confirma con
fuente independiente: se retira de la lista de vigilancia.** Coste de los datos: ≈ 20,8 $ del crédito gratuito.
