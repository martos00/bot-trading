# PREREGISTRO C83 — Segunda fuente de dos candidatas de futuros: oro D−2 09:30-10:00 corto y Nikkei Q−2 20:00-21:00 corto — 28-oct-2026

Redactado y subido a git ANTES de calcular con esta fuente.

## Origen (futuros, Databento)
1. **Oro corto el antepenúltimo día hábil del mes (D−2), 09:30 → 10:00 NY** (B18): descubrimiento −7,28 pb (t −3,86); confirmación
   2018-26 −8,27 pb (t −2,63), 89 % de años; coste 0,74. Mecanismo candidato: compras de dólares de fin de mes (el mismo día que E9,
   yen largo D−2: dólar fuerte) → oro (en dólares) más barato.
2. **Nikkei corto el penúltimo día hábil del trimestre (Q−2), 20:00 → 21:00 NY** (B14, NKD): −16,9 pb (t −3,36) / −14,1 pb (t −3,03),
   78 % de años; coste 2,5. 20:00 NY = 09:00-10:00 de Tokio (apertura). Mecanismo candidato: ventas de fin de trimestre (cierre del año
   fiscal en marzo, reequilibrio de fondos).

## Regla (segunda fuente: HistData, hora de NY con cambio de hora)
1. XAUUSD M1: D−2 = antepenúltimo laborable (lun-vie con datos) del mes. Corto del cierre del minuto 09:29 al del 09:59.
2. JPXJPY M1: Q−2 = penúltimo laborable de marzo, junio, septiembre y diciembre. Corto del cierre del minuto 19:59 al del 20:59 NY.
Periodo 2010-2026-09.

## Criterio (2 pruebas, Bonferroni unilateral 0,05/2)
Con el signo previsto (negativo): t (Newey-West) ≥ 1,96, ≥ 60 % de años con el signo, y |media 2018-2026| > coste CFD de FTMO
(oro 1,45 pb; Nikkei 2,5 pb, sin medir). Pasa → candidata para preregistrar como estrategia. Falla → cerrado. Contador +2.
