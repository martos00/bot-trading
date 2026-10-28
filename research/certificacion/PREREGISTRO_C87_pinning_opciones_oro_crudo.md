# PREREGISTRO C87 — "Pinning" el día de vencimiento de las opciones mensuales sobre futuros de oro (OG) y crudo (LO) — 28-oct-2026

Redactado y subido a git ANTES de calcular. Familia nueva en el proyecto: flujo de cobertura obligado de los creadores de mercado con
opciones que vencen (gamma). Si están largos de gamma en los strikes con mucho interés abierto, su cobertura compra por debajo y vende
por encima del strike → el precio tiende a acercarse a él el día del vencimiento. La literatura reciente (2026) no lo reproduce en el
S&P 500; en oro y crudo no lo hemos encontrado medido. Operable en una cuenta de fondeo de futuros (intradía, cierra antes de las 16:45).

## Datos
QuantConnect (AlgoSeek): futuros GC y CL a 1 minuto (hora de NY verificada, desfase 0) y cadenas de opciones sobre futuros con interés
abierto. Periodo: desde que haya datos (oro 2013) hasta 2026-09. Días: aquellos en que vence la serie mensual de opciones (la
cadena con vencimiento = ese día).

## Regla (igual para los dos)
- 09:31 NY: P0 = precio del futuro subyacente. Entre los strikes de la serie que vence ese día a ±1,5 % de P0, K* = el de mayor
  interés abierto total (call + put). Si |K* − P0| / P0 < 0,10 %, no se opera (ya está en el strike).
- Dirección = signo de (K* − P0). Posición en el futuro subyacente de 09:31 hasta la hora del vencimiento: **oro 13:30, crudo 14:30 NY**.
- Rentabilidad = dirección × ln(P_salida / P0), en pb.

## Criterio (2 pruebas, signo previsto positivo)
t (Newey-West) ≥ 2,24; media > 0 en la primera mitad (≤ 2018) y en la segunda (≥ 2019); media de la segunda mitad > coste del futuro
(oro 0,74 pb, crudo 2,0 pb). Informativo: % de aciertos, distancia media a K*, y el mismo cálculo en días sin vencimiento (strike más
cercano de la serie siguiente) como control. Lo que pase → simulación de cuenta de fondeo y, si sale bien, bot. Contador +2.
