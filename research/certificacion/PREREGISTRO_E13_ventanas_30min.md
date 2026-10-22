# Pre-registro E13 — Afinar a 30 minutos las ventanas de las ventajas certificadas (opción 1) — 22-oct-2026
Redactado y enviado a git ANTES de calcular a 30 minutos. Objetivo: subir el Sharpe por operación sin inventar ventajas nuevas.
## Candidatas (inicio × fin, en hora NY; incluye la ventana actual)
- E1 EURUSD corto (todos los días hábiles sin festivos TARGET): inicio {05:00, 05:30, 06:00, 06:30} × fin {07:30, 08:00, 08:30}. FXCM M1.
- E9 USDJPY largo (D−2): inicio {06:30, 07:00, 07:30} × fin {07:30, 08:00, 08:30} (fin > inicio). FXCM M1.
- E11 cesta yen fuerte (último día hábil del trimestre; USDJPY+EURJPY+GBPJPY): inicio {00:00, 00:30, 01:00, 01:30} × fin {01:30, 02:00, 02:30, 03:00}. FXCM M1.
- E8 oro largo (viernes): inicio {15:30, 16:00, 16:30} × fin 16:55. GC 1 min (gc_vie).
- E10 plata larga (víspera de festivo NYSE): inicio {15:30, 16:00, 16:30} × fin 16:55. SI 1 min (se descargan solo esos días, ≈ 0,15 $).
## Regla de decisión (fijada ahora)
Medida = media neta / desviación por operación (Sharpe por operación; neto con BID/ASK reales en FXCM, coste fijo en futuros: GC 0,74, SI 2,3 pb).
1) En el DESCUBRIMIENTO (FX 2012-2018; futuros 2010-2017) se elige la candidata con mayor medida.
2) Se adopta SOLO si en la CONFIRMACIÓN (FX 2019-2026; futuros 2018-2026) su medida ≥ la de la ventana actual y su t (NW) ≥ 2,0. Si no, se queda la actual.
Contador +5 (una decisión por ventaja).
