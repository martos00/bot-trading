# PREREGISTRO C117 — Ventajas descartadas por coste que en CFD de Upcomers podrían compensar

Redactado y subido a git ANTES de calcular (12-nov-2026).

## Revisión del catálogo (qué se descartó solo por coste y si el CFD es más barato)
- Divisas (yen en Tokio P3 +0,26 pb ejecutable; rebote del fixing del BCE +0,34 pb; Asia invertida): en Upcomers la divisa paga
  ~0,1 pb de spread + 5 $/lote por ejecución (≈ 0,43 pb por lado): NO es más barata que antes → no se prueban.
- Plata viernes 16:30-17:00 (B18/B19), platino última media hora (B20), bonos (C96): spreads CFD de plata 7-9 pb; platino y bonos sin medir
  y normalmente caros → no se prueban.
- Nasdaq 01-03 NY (C82): tras publicarse +0,58 pb, t 1,02 → no hay ventaja que salvar.
- **Ethereum 21→23 UTC (C2, certificada: +6,85 pb post-publicación, t 2,97)**: descartada antes porque el CFD de FTMO costaba ≈ 6,5 pb;
  en Upcomers la cripto cuesta spread + 0,04 % por ejecución (BTC medido 1,2 pb ida y vuelta) → **se prueba**.

## Pruebas (2 → Bonferroni: t ≥ 1,96 unilateral al 5 % / 2)
Base: cartera CFD de C116 (con bitcoin peso 0,2 y oro 16:55), control de volatilidad, 2018-03-26 → 2026-09-30.
| | Regla | Coste supuesto |
|---|---|---|
| N1 | Añadir ETH largo 21→23 UTC laborables, peso 0,2 (Binance ETHUSDT 1 h) | 1,5 pb ida y vuelta (0,8 de comisión + 0,7 de spread supuesto, sin medir) |
| N2 | Sustituir bitcoin 0,2 por cesta BTC 0,1 + ETH 0,1 | BTC 1,2 pb, ETH 1,5 pb |
Informativo (no decide): N1 con ETH a 3 pb.

## Criterio (igual que C116)
1. Sharpe con control de volatilidad sube ≥ 0,05 en total y sube en 2018-21 y en 2022-26.
2. ETH neto del coste: media > 0 con t ≥ 1,96 en 2018-2026.
Si pasan las dos, se elige la de mayor ΔSharpe total (regla fijada aquí). Antes de activarla hay que medir el spread real de ETH en
Upcomers con el script de costes; si supera 2 pb, no se activa.
