# Pre-registro P1 — RSI(2)<5 de Connors con dimensionamiento por volatilidad (hipótesis propia)

Redactado antes de calcular. **Advertencia de selección:** la señal (H75f) se eligió tras ver su
resultado fuera de muestra 2008-2026 entre 6 variantes. Por tanto P1 **no puede validarse con datos
de 1993-2026**; esta prueba solo mide si el dimensionamiento resuelve el incumplimiento de la pérdida
diaria. Cualquier validación exigirá datos posteriores al 19-oct-2026 (forward test en demo).

## Reglas
- Entradas y salidas idénticas a H75f (SPY > SMA200 y RSI2 < 5 → compra al cierre; salida al cierre
  por encima de la SMA5).
- Exposición fijada en la entrada: min(4, 1% / σ20), con σ20 = desviación típica de los 20 últimos
  rendimientos diarios de SPY. Parámetros fijados a priori por la puerta de viabilidad de fondeo
  (volatilidad diaria objetivo 1%); no se probarán otros valores.
- Costes CFD como en H75 (spread 1 pb ida y vuelta + financiación (tipo + 2,5%)/360 sobre el nocional).

## Medidas
Comparación con H75f a apalancamiento 1x: P(superar) FTMO 2-Step y FundedNext, P(incumplir
pérdida diaria), días hasta superar, percentil 1 del P&L diario. Éxito si la P(incumplir pérdida
diaria) baja a menos de la mitad sin reducir la P(superar). N acumulado = 89.
