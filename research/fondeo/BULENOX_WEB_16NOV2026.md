# Bulenox: lo que dice su web (leído 16-nov-2026)
Fuentes: bulenox.com, bulenox.com/accounts-pricing, bulenox.com/faq (solo títulos), legal/Bulenox-Rates.pdf (act. 11-ago-2026).
No se pudieron leer: /help (403), respuestas del FAQ (plegadas), pestañas Master/Qualification del help-center, Terms_of_Use.pdf.
- Mercados en la hoja de tarifas: GC, MGC, SI, 6J. **NKD, SIL y MJY no aparecen** (sin confirmar si se pueden).
- Horario: «Trade until 15:59 CT» (= 16:59 ET) → la plata del viernes hasta 16:57 cabe.
- Qualification 150K: 325 $ pago único, objetivo 9.000 $, pérdida hasta 4.500 $ (trailing o EOD, se elige al comprar), 15 contratos,
  sin días mínimos, «No daily loss limit» (la página se contradice), acceso válido 30 días. No hay 250K.
- Master: sin cuota mensual; hasta 90 % del beneficio; máx. 5 cuentas Master/Fast Track/Momentum a la vez; exámenes ilimitados.
- Sin leer: activación, frecuencia y topes de cobro, consistencia, colchón, qué pasa tras 3 cobros, copiador.
Ya confirmado antes por el soporte: las Master siguen activas mientras se mantengan; tras 3 retiros en al menos una Master se te «considera» para real.

## Reglas de retiro (página copiada por el usuario, 16-nov-2026)
≥ 10 días de trading por periodo (empieza al completarse el pago anterior); mín. 1.000 $; máx. 2.000 $ (150K) los 3 primeros, luego < 50 %
de la ganancia total de la Master; reserva 4.600 $ sobre el inicial tras el cobro; consistencia 40 % (1.er cobro desde el inicio, con la
reserva incluida; se reinicia tras cada cobro); 90 % para el trader; pagos los miércoles (solicitud hasta el viernes 23:59 CT);
W-8BEN firmado a mano + ID; ACH/transferencia o PayPal. Simulación: research/certificacion/bulenox_150k.py / .txt

## Respuestas del soporte (16-nov-2026; parecen de su asistente automático y citan webs de terceros y Reddit)
- Tras 3 cobros Bulenox PUEDE pasarte a cuenta real cuando decida; si no firmas, cierran la Master sin más pagos. Puede pasar a la vez otras Master con ≥ 1 cobro.
  La cuenta real empieza de cero con pérdida 4.500 $ EOD (150K). Beneficio de la Master no pasa a la real.
- Master 150K: pérdida 4.500 $ que se fija en 150.100 $ al llegar a 154.600 $. Con la opción EOD, límite diario 3.300 $ (se quita al fijarse).
- Activación Master 150K: 498 $ (pago único).
Simulación: research/certificacion/bulenox_150k_real.py / .txt (escenarios: la Master acaba 0, 3, 6 meses o nunca tras el 3.er cobro).
