# PREREGISTRO E8b — Oro largo el viernes 16:00 → 16:45 NY (salida adelantada por el horario de FTMO) — 27-oct-2026

Redactado y subido a git ANTES de calcular el tramo 16:00 → 16:45.

## Motivo (impuesto por la plataforma, no por resultados)
En FTMO el XAUUSD cierra el viernes a las 23:50 del servidor = 16:50 NY (captura de la especificación del símbolo, 27-oct-2026).
E8 sale a las 16:55 NY, así que no se puede ejecutar. La salida se adelanta a 16:45 NY: el último minuto que deja los
5 minutos de margen antes del cierre que ya usa el EA (`InpMinAntesCierre = 5`). Ninguna otra hora se probará.

Aviso de transparencia: ya se conocen tramos vecinos (C45b, descriptivo): 16:00→16:55 +3,26 pb y 16:30→16:55 +2,01 pb en el
futuro. El reparto entre 16:30-16:45 y 16:45-16:55 no se ha calculado. La hora 16:45 la fija la plataforma, no ese dato.

## Datos (ya en disco)
1. **Principal**: futuro GC 1 minuto (Databento, los mismos viernes que C45b, sin cambio de contrato en el día).
2. **Segunda fuente**: HistData XAUUSD M1 (contado, BID).
Periodo 2010-06 → 2026-09. Precio de entrada = cierre del último minuto < 16:00 (dentro de los 10 minutos previos); salida = cierre
del último minuto ≤ 16:44 (es decir, el precio a las 16:45), dentro de los 10 minutos previos. Rentabilidad logarítmica, solo viernes.

## Criterios (los mismos de C45, más el coste de FTMO)
- Futuro: media > 0 con t (Newey-West) ≥ 2,0; ≥ 60 % de años positivos; 2018-2026 > 0; y media 2018-2026 > 1,45 pb
  (coste FTMO: spread mediano medido 1,29 pb + comisión 0,0007 % por lado ≈ 0,14 pb).
- Contado HistData: media > 0 con t ≥ 2,0 en 2010-2026 y 2018-2026 > 0.
- Pasa todo → E8 se reactiva en FTMO con salida 16:45 NY. Falla algo → el oro sigue desactivado en FTMO, sin probar otras horas.
- Informativo: 16:45 → 16:55 (lo que se pierde). Contador +1.
