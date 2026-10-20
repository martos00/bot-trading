# Certificación C5 — Inversión en Asia: yen y dólar australiano se APRECIAN en su horario local

Redactado y enviado a git ANTES de descargar ni calcular nada con estos datos (20-oct-2026).

## Origen (hallazgo a posteriori, declarado)
En C3 (FXCM 2012-2026), al contrario que en Breedon-Ranaldo (1997-2007):
- USD/JPY en horario de Tokio (08:00 → 15:00 Tokio): −1,43 pb/día, t = −3,17 (yen se aprecia).
- AUD/USD en horario de Sídney (10:00 → 16:00 Sídney): +2,13 pb/día, t = +4,20 (dólar australiano se aprecia).
- EUR/JPY en horario de Tokio: −0,82 pb/día, t = −1,84 (mismo sentido que el yen).
Correlación entre las dos primeras: 0,03; con la sesión europea del EUR/USD: ≈ 0,01. Si es real, diversifica.
Como la hipótesis nace de mirar 2012-2026, **solo se puede certificar con datos no usados**.

## Factor (sentido "invertido")
Media simple diaria de: venta de USD/JPY de 08:00 a 15:00 Tokio y compra de AUD/USD de 10:00 a 16:00 Sídney.
Días laborables en la zona horaria de cada sesión. Precio = cierre del último minuto ≤ hora (tolerancia 5 min).

## Datos
HistData M1 (BID, hora de Nueva York con cambio de hora, verificada), **2008-01 → 2011-12**: posterior a la muestra del
estudio original y no usado por nosotros para estas sesiones (H80 miró franjas de 1-2 h de USD/JPY desde 2010 en hora de
NY; contaminación leve, declarada). Auditoría `calidad_datos`; los días en huecos se excluyen.
Informativo: 2003-2007 (período del estudio, donde ellos encontraron el signo normal; aquí no decide nada).

## Potencia (calculada antes con 2012-2026)
Sharpe del factor ≈ 1,3 → t esperada ≈ 2,6 con 4 años si el efecto es igual de fuerte.

## Criterios de certificación (todos)
- Factor 2008-2011: media > 0 con t de Newey-West unilateral ≥ 1,645.
- Ambos pares con el signo "invertido" en 2008-2011.
- Factor positivo en ≥ 3 de los 4 años.
Si se certifica: cartera EUR/USD (C1) + factor asiático en el paso 3, con costes de USD/JPY y AUD/USD.
