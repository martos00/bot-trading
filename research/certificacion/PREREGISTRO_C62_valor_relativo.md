# Pre-registro C62 — Valor relativo: oro/plata y Brent/WTI vuelven a su media (reversión del diferencial) — 22-oct-2026
Redactado y enviado a git ANTES de calcular. Tipo de ventaja nuevo en el proyecto para estos mercados (C32 probó solo SEK/NOK).
## Regla (idéntica para los dos pares)
Diario, cierres a las 16:00 NY. Oro/plata: GC c.0 y SI c.0 (Databento curva, diario); Brent/WTI: HistData BCOUSD y WTIUSD (precio de las 16:00 NY).
s = ln(A) − ln(B); z = (s − media de 60 días) / desviación de 60 días (ambas hasta el día anterior). Entrada si |z| > 2: largo de la pata barata y
corto de la cara (mismo nominal). Salida cuando z cambia de signo o a los 20 días. Una posición a la vez.
Coste por operación (dos patas, ida y vuelta): oro/plata 6 pb; Brent/WTI 8 pb; financiación 0,5 pb por día abierto.
## Tramos y criterios (Holm, k = 2)
Descubrimiento 2010-2017; **confirmación 2018 – 2026-09**: media neta por operación > 0 con t (NW) ≥ 2,0 tras Holm, ≥ 60 % de años positivos.
Informativo: número de operaciones, días medios abiertos, peor operación. Contador +2.
