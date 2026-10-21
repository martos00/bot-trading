# Resultados C10 — Gotobi del yen y prima del dólar en días de la Fed

Pre-registro: `PREREGISTRO_C10_gotobi_fomc_fx.md` (commit 317ecff). Script `c10_gotobi_fomc_fx.py`, salida `c10_resultados.txt`.
Corrección declarada del pre-registro: la variante informativa "sin rollover" se calcula desde las 08:00 Tokio (las 05:00
escritas en el pre-registro siguen antes del rollover); es solo informativa.

## G — Gotobi (compra de USD/JPY 03:00 → 09:55 Tokio los días 5, 10, 15, 20, 25 y fin de mes)
| | Resultado |
|---|---|
| Descubrimiento HistData 2003-2011 | +6,2 pb, t 4,87, 7/9 años |
| Confirmación FXCM 2012-2026 ejecutable (ASK/BID reales, comisión, deslizamiento, swap 0,5 pb) | **+3,7 pb, t 4,90**, 12/15 años, coste 1,45 pb (3,6×) |
| Correlación con E1 | 0,03 |
**Cumple los criterios pre-registrados.** Comprobaciones posteriores (no pre-registradas, decisivas):
| Precio medio | 2012-2022 | **2023-2026** |
|---|---|---|
| Días gotobi | +6,5 pb (t 7,99) | **+0,7 pb (t 0,44)**; ejecutable −0,8 pb |
| Resto de días, misma ventana | +1,1 pb | −1,7 pb |
| Diferencia gotobi − resto | 4,7 pb (t 5,0, toda la muestra) | 2,4 pb (t 1,17) |
El efecto es real y propio de los días gotobi durante 20 años, pero **desde 2023 (año en que se publicó el estudio de
Bessho et al.) ya no es rentable**: ejecutable negativo en 2023, 2024 y 2025. Veredicto: **certificada históricamente, no
operable hoy**. Se vigila: si en un forward test de ≥ 12 meses vuelve a ser positiva, se reconsidera con un pre-registro nuevo.

## F — Corto en USD contra la cesta el día del FOMC
Descubrimiento 2003-2011: +20,5 pb (t 2,15). Confirmación 2012-2026 ejecutable: +6,2 pb (t 1,14), 9/15 años. **No certificada.**
