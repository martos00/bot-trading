# Pre-registro C20 — "Divisa local débil en su horario" en seis divisas no probadas (21-oct-2026)

Redactado y enviado a git ANTES de descargar los datos y de calcular ningún resultado.

## Motivo
Es el único mecanismo que ha sobrevivido en todo el proyecto (C1/C3: EUR y GBP se deprecian frente al USD en horario europeo;
Breedon y Ranaldo, JMCB 2013, lo documentan en muchas divisas: las empresas de cada país compran divisa extranjera en su
horario laboral). No se ha probado en: corona sueca, corona noruega, zloty, forinto, rand y lira turca, todas en horario
europeo (Johannesburgo y Estambul están en husos europeos). Se excluye el peso mexicano (su horario coincide con el de EE. UU.,
donde se espera el efecto contrario para el dólar).

## Regla (idéntica a la sesión europea de C3)
Rentabilidad de USD/xxx de las 07:00 de Londres a las 08:00 de Nueva York, cada día laborable. Signo previsto: positivo
(la divisa local se deprecia). Pares: USDSEK, USDNOK, USDPLN, USDHUF, USDZAR, USDTRY. Datos: HistData M1 (BID, hora de NY
con horario de verano), 2010 → 2026-09; precio = cierre del último minuto ≤ hora (tolerancia 5 min); días con hueco excluidos.

## Tramos y criterios
- **Prueba principal: factor = media simple de los seis pares.** Descubrimiento 2010-2017: media > 0. Confirmación 2018 → 2026-09:
  (1) media > 0 con t de Newey-West ≥ 2,0; (2) positiva en ≥ 60% de los años.
- Pares por separado: informativos, con corrección de Holm (6 pruebas) en confirmación; la lira turca se informa también
  sin 2018, 2021 y 2023 (crisis cambiarias), solo como descripción.
- Costes: los datos son solo BID; antes de operar cualquier par habrá que medir su spread real a esas horas (script de
  costes de MT5). Referencia aproximada para informar (no decide): SEK 3, NOK 3, PLN 4, HUF 5, ZAR 6, TRY 15 pb ida y vuelta.
Contador +1 (N ≈ 1.176). Si falla, se descarta sin cambiar horas ni pares.
