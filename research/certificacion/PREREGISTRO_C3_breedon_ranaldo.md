# Certificación C3 — Réplica fiel de Breedon & Ranaldo: "cada divisa se deprecia en su horario local"

Redactado y enviado a git ANTES de descargar los datos nuevos (20-oct-2026).

## Fuente (leída completa: SNB WP 2011-04 y QMUL WP 694, abril 2012; publicado en JMCB 45(5), 2013)
Datos EBS 1997 → jun-2007, seis pares. Tabla 1 (horario local, según horario de los futuros):
EE. UU. 08:00-16:00 (Nueva York) · Europa 07:00-15:00 (Londres) · Japón 08:00-15:00 (Tokio) · Australia 10:00-16:00 (Sídney),
con los cambios de hora de cada región. Rentabilidad de sesión = punto medio al inicio y al final de la sesión, "apertura a
cierre" o "apertura a apertura" cuando el otro mercado abre con el primero aún abierto (EUR/USD: sesión europea 2-8 h NY).
Tabla 2 (todas del signo previsto y significativas salvo USD/JPY en horario de EE. UU.); estrategia neta de costes en EBS
rentable solo en EUR/USD: venta por la mañana (Sharpe 1,3) y compra por la tarde (Sharpe 0,9).

## Las 12 sesiones y el signo previsto (divisa base débil en su horario, fuerte en el de la otra)
| Par | Sesión | Inicio → fin | Signo previsto |
|---|---|---|---|
| EUR/USD | Europa | 07:00 Londres → 08:00 NY | − |
| EUR/USD | EE. UU. | 08:00 → 16:00 NY | + |
| GBP/USD | Europa | 07:00 Londres → 08:00 NY | − |
| GBP/USD | EE. UU. | 08:00 → 16:00 NY | + |
| USD/CHF | Europa | 07:00 Londres → 08:00 NY | + |
| USD/CHF | EE. UU. | 08:00 → 16:00 NY | − |
| USD/JPY | Japón | 08:00 → 15:00 Tokio | + |
| USD/JPY | EE. UU. | 08:00 → 16:00 NY | − (el estudio no lo encontró significativo) |
| EUR/JPY | Europa | 07:00 → 15:00 Londres | − |
| EUR/JPY | Japón | 08:00 → 15:00 Tokio | + |
| AUD/USD | Australia | 10:00 → 16:00 Sídney | − |
| AUD/USD | EE. UU. | 08:00 → 16:00 NY | + |
Días: lunes-viernes en la zona horaria de la sesión. Ningún tramo toca las 17:00 NY.

## Datos (todos posteriores a la muestra del estudio)
FXCM, velas M1 BID y ASK públicas, **2012-01 → 2026-09**, punto medio al cierre del último minuto ≤ hora (tolerancia 5 min).
Comprobación con HistData (BID) en EUR/USD, GBP/USD y USD/JPY (correlación diaria).

## Criterios de certificación por sesión
- Con el signo previsto, t de Newey-West (5 rezagos) unilateral significativa con corrección de **Holm-Bonferroni para
  12 pruebas** al 5% (umbral de 2,64 para la más significativa, bajando hasta 1,645).
- Del signo previsto en ≥ 9 de los 15 años (2012-2026).
- Concordancia con HistData donde exista: correlación diaria ≥ 0,9.

## Avisos de contaminación (declarados)
- EUR/USD sesión europea contiene la franja ya certificada C1 (06-08 NY): no es independiente de C1.
- H80 ya examinó franjas de 1-2 h de EUR/USD, GBP/USD y USD/JPY en 2010-2026: las sesiones completas son hipótesis definidas
  por el estudio, no por nosotros, pero no se han mirado a ciegas. USD/CHF, EUR/JPY y AUD/USD son totalmente nuevos.

## Después (paso 3, no decide la certificación)
Costes por sesión y cartera con las sesiones certificadas: correlaciones, Sharpe conjunto, simulación de fondeo.
