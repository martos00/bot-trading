# Pre-registro C64 — Flujos programados no probados: MSCI, Russell, triple hechicería, vencimiento del VIX, dividendos japoneses — 22-oct-2026
Redactado y enviado a git ANTES de calcular. Mismo tipo de mecanismo que las ventajas certificadas (flujos forzados con fecha conocida).
## Eventos y ventanas (hora NY). Signo NO fijado (dos colas): se prueba |t|
F1 MSCI (último día hábil de feb, may, ago, nov): ES, NQ y RTY 15:00 → 16:00 (media de los tres).
F2 Russell (último viernes de junio): RTY 15:00 → 16:00.
F3 Triple hechicería (tercer viernes de mar, jun, sep, dic; si festivo, día hábil anterior): ES 15:00 → 16:00.
F4 Vencimiento del VIX (miércoles = tercer viernes del mes siguiente − 30 días; si festivo, día hábil anterior): ES 09:30 → 10:00 (1 min Databento).
F5 Dividendos japoneses (antepenúltimo día hábil de marzo y septiembre = último día con derecho, aprox.): JPXJPY (HistData) 01:00 → 02:00 (cierre de
   Tokio), y su reverso el día siguiente.
Datos: ES 1 min (Databento), NQ/RTY h1 (Databento), JPXJPY HistData. 2010-06 – 2026-09 completo (pocos casos: no se parte en tramos).
## Criterios
Holm sobre las 6 pruebas (F5 cuenta 2): |t (NW)| con p bilateral ≤ 0,05/(6−j); además ≥ 60 % de años con el signo y |media| ≥ 3 × coste (ES 0,73,
NQ 0,3, RTY 1,2, JPX 2,0 pb). Lo que pase necesita confirmación con otra fuente antes de operar. Contador +6.
