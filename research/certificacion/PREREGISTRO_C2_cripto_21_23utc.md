# Certificación C2 — Subida de cripto entre las 21:00 y las 23:00 UTC (réplica en Ethereum)

Redactado y enviado a git ANTES de descargar los datos de Ethereum (20-oct-2026).

## Origen
H78 (Quantpedia, feb-2022, BTC en Gemini 2015-2022): tras la publicación (2022-02-04 → 2026-09-30) BTC sigue subiendo en
esa franja: +5,2 pb/día, t = 3,0, igual en Binance y Coinbase, control de hora aleatoria p = 0,004.
La fuente solo estudió Bitcoin. **Ethereum no se usó para descubrir el efecto**: es una réplica en otro activo, aunque no
independiente del todo (ETH y BTC están muy correlacionados; se informará de la correlación de la franja).

## Datos y regla (idéntica a H78)
Binance ETHUSDT spot, velas de 1 h. Todos los días. Largo a la apertura de la vela de 21:00 UTC, cierre a la apertura de
la de 23:00 UTC. Rentabilidad simple bruta (sin costes: esto es certificación de la ventaja, no de la estrategia).

## Criterios (todos)
- **E1** ETH, post-publicación 2022-02-04 → 2026-09-30: media > 0 con t de Newey-West ≥ 2,0.
- **E2** Mejor que el control: misma duración con hora de inicio aleatoria en los mismos días, p < 0,05 (10.000 réplicas).
- **E3** Positiva en ≥ 3 de los 5 años (2022-2026).
- **E4** Informativo: correlación diaria con la franja de BTC y resultado de ETH antes de 2022-02 (desde 2017-08).
Si E1-E3 se cumplen, junto con H78 (BTC, t = 3,0 en dos bolsas), la ventaja se da por **certificada**.
