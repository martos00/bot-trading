# Pre-registro C61 — Niveles redondos en divisas (Osler 2003, 2005): rebote al tocar y aceleración al cruzar — 22-oct-2026
Redactado y enviado a git ANTES de calcular. Tipo de ventaja nuevo en el proyecto (microestructura de órdenes, no calendario).
## Fuente (de memoria; no texto completo verificado)
Osler (JF 2003): las órdenes de toma de beneficios se concentran en cifras redondas → el tipo de cambio tiende a rebotar al llegar a ellas.
Osler (JIMF 2005): las órdenes stop se concentran justo detrás → al cruzarlas, el movimiento se acelera ("cascadas de stops").
## Regla
FXCM M1 BID/ASK (mid) 2012-2026: EURUSD, GBPUSD, AUDUSD, USDCAD, USDCHF (nivel = múltiplo de 0,0100) y USDJPY (múltiplo de 1,00).
Horario: 02:00-12:00 NY (Londres + NY, liquidez alta). Un evento por par, día y nivel (el primero).
- **R (rebote)**: primer minuto en que el mid llega a ±0,5 pip del nivel, viniendo de un lado (mid 15 min antes a > 5 pips del nivel en ese lado).
  Posición: en contra del avance (si venía de abajo, corto). Salida a los 30 min. Rentabilidad = −dirección × ln(mid t+30 / mid t).
- **C (cruce)**: primer minuto en que el mid supera el nivel en 3 pips en el sentido del avance tras haberlo tocado. Posición: a favor. Salida 30 min.
Coste real: medio spread a la entrada y a la salida + 0,45 pb de comisión.
## Criterios (Holm, k = 2)
Media de los 6 pares por evento. Descubrimiento 2012-2018 (informativo); **confirmación 2019 – 2026-09**: media neta > 0 con t (NW) ≥ 2,0 tras
Holm, ≥ 60 % de años positivos, bruto ≥ 3 × coste. Contador +2.
