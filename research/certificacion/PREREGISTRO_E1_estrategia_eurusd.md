# Pre-registro E1 — Estrategia sobre la ventaja certificada C1 (EURUSD, mediodía europeo)

Redactado y enviado a git ANTES de calcular ningún resultado de la estrategia (20-oct-2026). Paso 3 del plan del usuario:
montar la estrategia sobre una ventaja ya certificada. La señal no se toca: es exactamente la certificada.

## Reglas
- Cada día laborable de Nueva York: **venta de EURUSD a las 06:00:00 ET y recompra a las 08:00:00 ET**, a mercado.
- **Tamaño por volatilidad** (sin mirar el futuro): σ = desviación típica de la rentabilidad de la franja en los 60 días
  anteriores (sin incluir el día). Exposición = objetivo / σ (como múltiplo del capital), con tope de 10×.
  Dos niveles de riesgo fijados de antemano, **ambos se informan** (no se elige el mejor con los resultados):
  objetivo **0,5%** y **1,0%** de volatilidad diaria del capital. La elección entre ellos es una preferencia de riesgo del
  usuario, no un parámetro a optimizar.
- **Stop de catástrofe** a 4 σ por encima del precio de venta (protege los límites diarios de las firmas). Si el máximo de la
  franja lo toca, la operación sale en el stop con 0,5 pb de deslizamiento adicional.
- Filtro de ejecución: no se opera si faltan datos a las 06:00 o a las 08:00 (en la vida real: si el spread a las 06:00
  supera 1 pip).

## Datos
Serie certificada 2018-2026 (`c1_precios.csv`: FXCM y Dukascopy, punto medio) para la rentabilidad. Peor momento de la
franja = máximo de AskHigh de FXCM (o del cierre de minuto de Dukascopy en sus días) entre 06:00 y 08:00 ET: conservador.

## Costes (tres escenarios, de `PASO2_COSTES.md`)
Bajo 0,44 pb (FundingPips 2 $ i/v) · medio 0,53 pb (FTMO 3 $ i/v) · alto 0,79 pb (FTMO 3 $ por lado).

## Qué se informa (todo)
Por escenario de coste y nivel de riesgo: rentabilidad anual neta, Sharpe, t, drawdown máximo, peor día, años positivos,
nº de stops. Simulación de fondeo (`research/fondeo/simulador_fondeo.py`, Monte Carlo por bloques con incertidumbre de la
ventaja, 5.000 simulaciones) con FTMO 2-Step, FundedNext 2-Step y FundingPips 2-Step (8%/5%, diaria 5%, máxima 10%
estática, 3 días mínimos; reglas de fuentes de terceros), siempre junto a la **misma simulación sin ventaja** (media 0)
como referencia. No se ajusta nada para mejorar la probabilidad de superar la evaluación.

## Criterio para pasar a demo en tiempo real
Con el coste medido en la demo de la firma elegida (no con supuestos): neto > 0 con t ≥ 2 en 2018-2026 y probabilidad de
superar la evaluación claramente mayor que la referencia sin ventaja.
