# Pre-registro C30 — Semana de vencimiento de opciones en el S&P 500 y ventana previa al dato de empleo (21-oct-2026)

Redactado y enviado a git ANTES de calcular nada (el ES al minuto y el GC horario ya estaban descargados para otras pruebas;
el ZN horario se descarga después de este registro).

## X — Semana de vencimiento mensual de opciones (Stivers y Sun; literatura de "option expiration week")
Rentabilidades más altas en la semana del vencimiento mensual de las opciones (tercer viernes), atribuidas a la cobertura de
los creadores de mercado. Regla: largo del futuro ES del cierre de la sesión regular (16:00 NY) del viernes anterior al cierre
del tercer viernes del mes. Unilateral (+). Comparación: resto de semanas. Coste ES 0,6 pb + financiación implícita (nada extra
en futuros). Informativo: solo vencimientos trimestrales (marzo, junio, septiembre, diciembre).
## N — Ventana previa al dato de empleo (NFP, viernes 08:30 NY)
Oro (GC) y bono a 10 años (ZN), de las 17:00 NY del jueves a las 08:00 NY del viernes del dato (barras horarias Databento).
Sin predicción de signo (bilateral; el descubrimiento fija el sentido). Fechas: primer viernes del mes (aproximación declarada:
en algunos meses el dato sale el segundo viernes; no se corrige).

## Tramos y criterios (3 pruebas, Holm)
Descubrimiento 2010-06 → 2017; confirmación 2018 → 2026-09: signo previsto (o fijado) con t de Newey-West que supere Holm,
≥ 60% de años, bruto ≥ 3 × coste (ES 0,6 pb; GC 0,5 pb; ZN 1,8 pb). Contador +3 (N ≈ 1.204).
