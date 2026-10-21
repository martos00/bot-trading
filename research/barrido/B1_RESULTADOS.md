# B1 — Barrido amplio de ventajas operables en fondeo: RESULTADOS (21-oct-2026)

Pre-registro: `PREREGISTRO_B1_barrido_fondeo.md` (commit 10c4438, antes de descargar). Salida: `b1_resultados.txt`.
Motores: `../fase72/h80_motor.py` (F1), `b1_motor_f2.py` (F2), `b1_evaluacion.py`; zona horaria: `b1_zona_horaria.py`.

## Desviaciones declaradas
- Euro Stoxx (ETXEUR): HistData solo tiene 2010-2019 → excluido (sin tramo de confirmación).
- WTI: hueco de 670 días hábiles (dic-2023 → jun-2026) excluido; confirmación más corta.
- ASX (AUXAUD): la verificación de zona horaria es ambigua (mayor salto a las 17:30 NY); se mantuvo, marcado como dudoso.
- Reglas evaluadas: 640 (628 F1 + 12 F2), no 779, por lo anterior y por las franjas con < 250 días en el descubrimiento.
- Zona horaria verificada: DAX/CAC/FTSE con salto a las 03:00 NY (apertura europea), Hang Seng a las 20:00, WTI 09:00 y
  14:00, USDCAD 08:30, EURGBP 02:00-03:00: hora de Nueva York con cambio de hora, como en el resto del proyecto.

## Descubrimiento 2010-2017
|t| ≥ 2: 126 reglas (≈ 29 por azar); |t| ≥ 3: 37 (≈ 1,7 por azar). Hay estructura horaria real en el descubrimiento.
Ninguna regla de sesión de índice (F2: apertura-cierre y momentum intradía) llega a |t| ≥ 2 en ningún índice.

## Confirmación 2018-2026 (k = 37, Bonferroni t ≥ 3,00)
Cumplen los cuatro criterios 5 reglas, todas ventas de divisas que terminan a las 17:00 NY:
EURCHF 16-17 (t 24,1), EURGBP 16-17 (t 21,2), EURCHF 15-17 (t 21,2), EURGBP 15-17 (t 19,2), NZDUSD 16-17 (t 14,7).
**Comprobación de artefacto (prevista en el pre-registro):** la mayor parte ocurre entre 16:55 y 17:00 NY:
EURCHF +2,18 pb (t 28,9), EURGBP +2,23 (t 29,4), NZDUSD +3,02 (t 24,4), EURAUD +2,21 (t 27,5), USDCAD +1,30 (t 20,6),
frente a 15:00-16:55 de +0,08 a +0,77 pb. Es la caída del BID por el ensanchamiento del spread antes de la pausa diaria
(mismo artefacto que en H73 y H80): **no es operable. Ninguna se certifica.**
Lo que queda en 15:00-16:55 en los cruces del euro (+0,7 pb, t ≈ 5) es menor que su coste (1,0-2,0 pb) y no se certificó con
precio medio: no es operable aunque fuera real.
Casi-candidata: plata, venta 06:00-07:00 NY (bruto 2,32 pb, t 3,00, justo bajo el umbral 3,00; neta t 1,71; 9/9 años). No
cumple; además, 07:00 NY coincide con la subasta de la plata de Londres (12:00), posible efecto de fixing.

## Veredicto
El barrido de 640 reglas en 16 mercados nuevos **no encuentra ninguna ventaja nueva operable en fondeo**. Las únicas reglas
que pasan la confirmación son un artefacto de los datos BID. La mejor ventaja real y operable sigue siendo la del EUR/USD
en la sesión europea (C1). N acumulado del proyecto: 364 + 640 = 1.004 reglas probadas.
