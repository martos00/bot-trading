# Pre-registro B1 — Barrido amplio de ventajas operables en cuentas de fondeo

Redactado y enviado a git ANTES de descargar los datos de estos mercados (21-oct-2026).
Petición del usuario: buscar todas las ventajas posibles hasta encontrar la mejor real para fondeo. Riesgo principal:
buscar entre cientos de reglas fabrica falsos positivos. Defensa: universo y reglas fijados aquí, descubrimiento y
confirmación en tramos distintos, corrección por número de pruebas, certificación con otra fuente y puerta de costes.

## Universo (instrumentos que ofrecen las firmas CFD y que este proyecto no ha examinado)
Índices: DAX (GRXEUR), FTSE 100 (UKXGBP), Nikkei 225 (JPXJPY), Euro Stoxx 50 (ETXEUR), CAC 40 (FRXEUR), ASX 200 (AUXAUD),
Hang Seng (HKXHKD). Materias primas: plata (XAGUSD), WTI (WTIUSD), Brent (BCOUSD). Divisas: EURGBP, EURCHF, GBPJPY, AUDJPY,
NZDUSD, USDCAD, EURAUD. Datos HistData M1 (BID), 2010-2026; zona horaria verificada antes de usar cada instrumento
(salto de actividad en la apertura de su mercado); `calidad_datos` y exclusión de huecos.

## Familias de reglas (sin parámetros que ajustar)
- **F1 franjas horarias**: inicio en cada hora en punto de NY (0-23), duración 1 y 2 h, excluyendo todo lo que toque
  17:00-18:00 NY → 45 por instrumento (765). Dirección = signo en el descubrimiento.
- **F2 sesión de contado de cada índice** (7 índices × 2 = 14 reglas): (a) largo de apertura a cierre de la sesión local;
  (b) momentum intradía: en la última media hora, posición en el sentido de la primera media hora (Gao et al. 2018).
  Sesiones locales: DAX, CAC y Euro Stoxx 09:00-17:30 Fráncfort/París; FTSE 08:00-16:30 Londres; Nikkei 09:00-15:00 Tokio;
  ASX 10:00-16:00 Sídney; Hang Seng 09:30-16:00 Hong Kong.
Total: **779 reglas**. Todas intradía (sin swap). N acumulado del proyecto: 364 + 779 = 1.143.

## Tramos y criterios
- Descubrimiento 2010-2017 (o desde el inicio de los datos si es posterior): pasa |t_NW| ≥ 3,0.
- Confirmación 2018-2026-09: mismo signo y t unilateral ≥ umbral de Bonferroni para k seleccionadas (5%); neto del coste
  base t ≥ 2; ventaja bruta ≥ 2 × coste base; positiva en ≥ 6 de 9 años.
- Costes base (CFD de fondeo, pb ida y vuelta, de fuentes de terceros; se medirán después con datos BID/ASK):
  DAX 0,8 · FTSE 1,2 · Nikkei 2,5 · Euro Stoxx 3,5 · CAC 1,5 · ASX 1,2 · Hang Seng 3,5 · plata 1,0 · WTI 0,6 · Brent 0,7 ·
  EURGBP 1,0 · EURCHF 1,2 · GBPJPY 1,8 · AUDJPY 1,5 · NZDUSD 1,4 · USDCAD 1,1 · EURAUD 2,0.
- Lo que se confirme pasa a **certificación** (otra fuente de datos con BID/ASK, spread real a esa hora, artefactos del
  BID, puerta final ventaja ≥ 3 × coste medido) y solo después a estrategia y simulación de fondeo.
- Ranking final de todo lo certificado (incluida C1) por Sharpe neto y compatibilidad con fondeo.
