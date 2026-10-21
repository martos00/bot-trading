# Pre-registro C28 — Días de informe y de vencimiento en grano, oro y ganado (21-oct-2026)

Redactado y enviado a git ANTES de descargar los precios y de calcular nada (solo se descargaron las fechas de los informes,
del archivo oficial del USDA, esmis.nal.usda.gov). Hipótesis común, por analogía con el gas natural (exploración F1): presión
vendedora antes de un dato o de un flujo forzado con fecha fija → el precio cae ese día. Signo previsto: negativo.

## W — Grano el día del WASDE (informe mensual del USDA, 12:00 NY)
Maíz (ZC), soja (ZS) y trigo (ZW): corto del cierre del día hábil anterior al cierre del día del informe. Factor = media de los tres.
## G — Oro antes del primer día de aviso de entrega (COMEX)
Meses de entrega activos: feb, abr, jun, ago, oct, dic. Primer día de aviso (FND) ≈ último día hábil del mes anterior.
Corto de oro (GC) del cierre de FND−6 al cierre de FND−1 (5 sesiones): liquidación de largos antes de la entrega.
## L — Ganado vacuno el día de "Cattle on Feed" (USDA, normalmente viernes a las 15:00 NY, tras el cierre)
Corto de ganado vivo (LE) del cierre del día hábil anterior al cierre del día del informe.

## Datos, tramos y criterios (3 pruebas, Holm)
Databento GLBX.MDP3, contrato continuo por volumen, cierres diarios, sin rentabilidades entre contratos distintos.
Costes (futuros, ida y vuelta, aprox.): ZC/ZS/ZW 6 pb de media, GC 1 pb, LE 2 pb.
Descubrimiento 2010-06 → 2017: signo previsto. Confirmación 2018 → 2026-09: media neta del corto > 0 con t de Newey-West que
supere Holm (3), ≥ 60% de años positivos, bruta ≥ 3 × coste, y distinta de un día/ventana normal (t ≥ 1,645).
Contador +3 (N ≈ 1.200).
