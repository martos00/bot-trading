# Certificación C4 — "Dólar débil en horario de EE. UU." (08:00 → 16:00 NY) con datos no usados

Redactado y enviado a git ANTES de descargar ni calcular nada con estos datos (20-oct-2026).

## Origen
C3 (réplica de Breedon-Ranaldo con FXCM 2012-2026): en la sesión de EE. UU. el dólar se deprecia en EUR/USD (t 2,31),
GBP/USD (t 2,05) y USD/CHF (t 2,40), sin superar la corrección de Holm por 12 pruebas. Las tres series se mueven juntas
(0,6-0,8) y no se mueven con la sesión europea (correlación del factor con EUR/USD Europa: −0,01): si fuera real,
diversificaría la cartera.
**Selección a posteriori declarada:** se eligen los tres pares porque fueron los que mostraron el efecto en 2012-2026 (USD/JPY
y AUD/USD no lo mostraron). Por eso la prueba se hace solo con datos que no se han usado para esta sesión.

## Factor
Media simple diaria de las tres rentabilidades de 08:00 a 16:00 NY con el signo previsto: + EUR/USD, + GBP/USD, − USD/CHF.
Lunes a viernes. Precio = cierre del último minuto ≤ hora (tolerancia 5 min).

## Datos
HistData M1 (BID; zona horaria de Nueva York con horario de verano, verificada en H69/H71), **2003-01 → 2011-12**.
- 2008-2011: posterior a la muestra del estudio (1997 → jun-2007) y no usado por nosotros para esta sesión.
- 2003-2007: dentro del período del estudio, pero con otra fuente de datos (réplica, no fuera de muestra).
H80 usó franjas de 1-2 h de EUR/USD y GBP/USD desde 2010 (no esta sesión de 8 h): contaminación leve en 2010-2011, declarada.

## Potencia (calculada antes con 2012-2026)
Sharpe bruto del factor 0,67 → t esperada ≈ 1,3 con 4 años y ≈ 2,0 con 9 años. **Prueba de poca potencia**: un resultado
negativo no demuestra que el efecto sea falso.

## Criterios de certificación (ambos)
- **Principal**: 2008-2011, media > 0 con t de Newey-West unilateral ≥ 1,645.
- **Secundario**: 2003-2011, t ≥ 2,0 y media positiva en ≥ 6 de 9 años.
Se informa también de cada par por separado y de USD/JPY y AUD/USD (si hay datos) a título informativo.
Si se certifica: cartera C1 + factor en el paso 3 (costes de 3 pares, correlación, Sharpe conjunto, fondeo).
