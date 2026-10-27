# PREREGISTRO E13 — Estrategia: Nikkei largo el 2.º día hábil del trimestre, 15:00 → 16:00 NY — 27-oct-2026

Base: B14 (futuro NKD, descubrimiento) + C60/C78 (CFD JPXJPY de HistData con la hora corregida: +16,2 pb, t 4,12, 15/16 años;
2018-26 +10,7 pb). Regla fija: largo JP225 de 15:00 a 16:00 NY el 2.º laborable (lun-vie, sin contar el 1 de enero) de enero, abril,
julio y octubre. Tamaño como el resto del EA: riesgo = `InpRiesgoPct` por operación con sigma de la misma ventana en los últimos 60
laborables; stop de catástrofe 4 sigmas; mismas protecciones. Simulación con costes 2,5 pb: Sharpe de la cartera 1,28 → 1,35 (2018-26).

**Condición para activarla** (fijada ahora): coste ida y vuelta medido en la cuenta (script `Comprobar_Cuenta_y_Costes_6_Ventajas`,
mediana a las 15:00 y 16:00 NY) ≤ 5 pb (< 1/2 de la ventaja reciente de 10,7 pb). Si es mayor, se queda desactivada. No se cambia la
hora ni el día por ningún resultado.
