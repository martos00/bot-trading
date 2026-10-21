# Gas natural los jueves (día del informe EIA): exploración (21-oct-2026) — NO certifica nada

Datos Databento NG (contrato continuo por volumen, sin rentabilidades entre contratos), 2010-2026; salida `ng_exploracion.txt`.
Todo esto se ha mirado DESPUÉS de ver C15 y la verificación con Databento: sirve para entender, no para certificar.

- **Solo el jueves:** media −40 pb (t −3,62); el resto de días entre −9 y −2 pb (ninguno significativo). 2010-2016 −33 pb,
  2017-2026 −46 pb. **15 de 17 años negativos.** Mediana −45 pb; quitando el 5% de jueves más extremos, −39 pb.
- **Estación:** mucho más fuerte en la de extracción (nov-mar, −75 pb, t −3,80) que en la de inyección (abr-oct, −17 pb).
- **Hora (barras horarias, hora NY):** la caída se concentra en **09:00-10:00, la hora antes del informe de las 10:30**
  (−12 pb, t −3,73; resto de días −0,8 pb), sigue a las 10:00-11:00 (−8,8 pb) y el resto del día (−9 pb); la noche aporta poco.
- Lectura posible (sin verificar): presión vendedora/coberturas antes de un dato de alto riesgo, del tipo "deriva previa al
  anuncio" pero con signo negativo; o prima de riesgo del anuncio al revés de lo que dice el estudio.

## Costes (orientativos)
Futuro NG: 1 tick (10 $) sobre ≈ 30.000 $ ≈ 3,3 pb + comisión ≈ 5 pb ida y vuelta → jueves completo (−40 pb) ≈ 8× coste;
ventana 09:00-10:25 (≈ −12/−15 pb) ≈ 2,5-3×. CFD de gas en firmas de fondeo: spreads habituales de 15-30 pb (a medir).
Sharpe aproximado del corto del jueves completo (futuro): ≈ 0,8-0,9 anual, correlación ≈ 0 con E1.

Siguiente paso: pre-registro de prueba HACIA DELANTE (`PREREGISTRO_F1_gas_jueves.md`), sin tocar la regla durante ≥ 50 jueves.
