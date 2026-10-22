# Pre-registro C45 — Confirmación independiente: oro largo el viernes 16:00 → 17:00 NY (hallazgo de B4) — 22-oct-2026
Redactado y enviado a git ANTES de descargar los datos de contado.
## Origen
B4 (barrido día × hora en futuros, pre-registrado) certifica según sus criterios GC viernes 16:00-17:00 NY largo: 2010-17 +3,20 pb
(t 4,21); 2018-26 +3,86 pb (t 4,38), 9/9 años, coste 0,74 pb. La plata (SI) a la misma hora +6,3 pb (t 3,68), 9/9 años, pero no pasa
el criterio de coste (2,3 pb). Mecanismo candidato: cobertura con oro ante el riesgo del fin de semana (mercado cerrado ~48 h).
Como con E1, se exige una segunda fuente independiente antes de operar.
## Regla
Datos: HistData XAUUSD y XAGUSD M1 (BID, hora EST fija → se convierte a hora de NY con horario de verano). Cada viernes (o último día
de la semana con sesión): largo del cierre del minuto 15:59 al cierre del último minuto ≤ 16:58 NY (el contado CFD cierra a las 17:00;
se sale 1-2 minutos antes como haría el EA). Coste de referencia del CFD del oro: 1,0 pb (se medirá en MT5).
## Criterios
Oro, 2010-06 – 2026-09: media bruta > 0 con t (NW) ≥ 2,0 y ≥ 60 % de años positivos; además 2018-26 > 0. Plata: informativo.
Informativo: el resto de días a la misma hora y el tramo 16:00-16:30 / 16:30-16:58. Si pasa → E-oro se pre-registra como estrategia
con el coste real medido en MT5 y entra en forward/demo. Contador +1.
