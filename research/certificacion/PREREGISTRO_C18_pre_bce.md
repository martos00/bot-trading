# Pre-registro C18 — Subida de la bolsa europea antes de las reuniones del BCE (Quantpedia 2025) — 21-oct-2026

Redactado y enviado a git ANTES de descargar los índices y de calcular ningún resultado (solo se descargaron las fechas).

## Fuente
Quantpedia (2025, investigación propia, no revisada; leído el resumen del agente): el DAX y el Euro Stoxx suben del cierre
del día D−2 al cierre de D−1 antes de las ruedas de prensa del BCE (datos desde 1998). Contradicción: Brusa, Savor y Wilson
(Review of Finance 2020) no encuentran prima de anuncio en bancos centrales distintos de la Fed. Mecanismo propuesto:
reducción de incertidumbre/posicionamiento antes del anuncio, como el pre-FOMC (que ya se apagó en EE. UU.).

## Datos y regla
- Fechas: base de datos EA-MPD del BCE (Altavilla et al.; hoja "Press Conference Window"), 315 reuniones 1999 → oct-2025.
- Índice: DAX (^GDAXI, Yahoo, cierres diarios); informativo: Euro Stoxx 50 (^STOXX50E, desde 2007).
- Regla: largo del cierre de D−2 al cierre de D−1 (sesiones con dato), D = día de la reunión.
- Coste CFD: 1,0 pb ida y vuelta + 2,0 pb de financiación por noche natural.

## Tramos y criterios
- Descubrimiento 1999-2012: media bruta > 0.
- Confirmación 2013 → oct-2025 (todos): (1) media neta > 0 con t ≥ 2,0; (2) bruta ≥ 3 × coste; (3) neta positiva en ≥ 60%
  de los años; (4) mayor que la media de un día normal (t ≥ 1,645). Aviso: no hay datos posteriores a la publicación (2025).
Contador +1 (N ≈ 1.173). La presión de dividendos (Hartzmark-Solomon) no se prueba: no hay calendario gratuito de pagos.
