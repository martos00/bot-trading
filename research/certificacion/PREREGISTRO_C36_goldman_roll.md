# Pre-registro C36 — Adelantarse al "Goldman roll" en diferenciales de calendario de energía — 21-oct-2026

Redactado y enviado a git ANTES de calcular nada con los datos de primer y segundo vencimiento (descargados para C34;
todavía no se ha calculado ningún diferencial).
## Fuente (de memoria / resúmenes; no texto completo verificado)
Mou (2011, "Limits to arbitrage and commodity index investment: front-running the Goldman roll"): los índices de materias
primas (S&P GSCI, BCOM) venden el primer vencimiento y compran el siguiente entre el 5.º y el 9.º día hábil de cada mes.
Esa presión ensancha el diferencial (2.º − 1.º); adelantarse comprando 2.º / vendiendo 1.º antes del periodo de roll era
rentable hasta 2010. Mecanismo: flujo forzado y predecible por calendario de un volumen enorme. Riesgo: muy publicado.
## Regla
Mercados: CL, HO, RB, NG (vencimiento mensual, el índice rueda todos los meses). Datos Databento diarios c.0 y c.1, sin
rentabilidades en días de cambio de contrato (instrument_id distinto), que se descartan.
Diferencial diario = rentabilidad log de c.1 − rentabilidad log de c.0 (largo 2.º vencimiento, corto 1.º).
Día hábil = sesiones presentes en los datos. Dos ventanas (Holm, k = 2), ambas con signo predicho positivo:
- **W1 adelantamiento**: rentabilidades de los 5 últimos días hábiles del mes anterior y de los días hábiles 1–4.
- **W2 periodo de roll**: rentabilidades de los días hábiles 5–9.
Unidad: una operación por mes y mercado = suma de los diferenciales diarios de la ventana − coste 4 pb (ida y vuelta del
diferencial: ~1 tic por pata y lado + comisión). Serie mensual = media de los 4 mercados.
## Tramos y criterios
Descubrimiento 2010-06–2014 (informativo). **Confirmación 2015-01 – 2026-09**: media neta > 0, t (Newey-West, 3) ≥ 2,0
tras Holm, ≥ 60 % de años positivos y bruto ≥ 3 × coste. Sin cambiar ventanas, mercados ni coste después de ver datos.
Contador +2. Aviso: requiere futuros reales (diferencial de calendario); no es operable con CFD de FTMO.
