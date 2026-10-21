# Pre-registro C11 — Impulso de la última media hora del S&P 500 cuando la gamma de los dealers es negativa (21-oct-2026)

Redactado y enviado a git ANTES de calcular ningún resultado (el fichero de GEX se descargó y solo se miró su cabecera).

## Origen y mecanismo
TikTok de @tradingstraty (transcripción leída): "opera la volatilidad, no la dirección", usando niveles de exposición gamma.
Versión estudiada: Baltussen, Da, Lammers y Martens (2021, *Journal of Financial Economics*, "Hedging demand and market
intraday momentum"): cuando los creadores de mercado de opciones tienen gamma negativa, cubren en el mismo sentido del
movimiento y lo amplifican al final del día; así, la rentabilidad del día hasta las 15:30 predice la de la última media
hora. H69 probó el impulso intradía sin condición y lo descartó; condicionado a la gamma no se ha probado.

## Datos
- GEX diario de SqueezeMetrics (`DIX.csv`, gratuito, desde 2011-05). Se usa el GEX del día anterior (conocido antes de abrir).
- S&P 500: HistData SPXUSD M1 (BID, hora de NY), 2011-05 → 2026-09. Precio = cierre del último minuto ≤ hora (tolerancia 5 min).

## Regla
Día t con GEX(t−1) < 0: a las 15:30 NY se toma posición en el sentido de la rentabilidad desde el cierre de las 16:00 de la
sesión anterior hasta las 15:30 de hoy; se cierra a las 16:00 (último minuto ≤ 16:00). Coste de CFD: 1,0 pb ida y vuelta.

## Tramos y criterios
- Descubrimiento 2011-05 → 2018: media bruta > 0.
- Confirmación 2019 → 2026-09 (todos): (1) media neta > 0 con t de Newey-West ≥ 2,0; (2) media bruta ≥ 3 × coste;
  (3) neta positiva en ≥ 60% de los años con ≥ 5 operaciones.
- Informativo: misma regla en días con GEX ≥ 0 y sin condición (debería ser menor); diferencia entre ambos; resultados de
  la regla del 80% (C9, reversión) separados por el signo del GEX (la teoría predice que la reversión funciona con gamma
  positiva). Contador +1 (N ≈ 1.163). Si falla, se descarta sin cambiar umbral ni horas.
