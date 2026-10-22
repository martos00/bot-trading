# Pre-registro C54 — Confirmación independiente de los hallazgos de B13 (cambio de trimestre × hora) — 22-oct-2026
Redactado y enviado a git ANTES de calcular con estas fuentes (EURJPY de HistData aún no descargado).
## Hallazgos de B13 (≈ 4 operaciones al año cada uno; ~30 casos por tramo)
1. EURUSD largo el primer día hábil del trimestre (Q+1), 15:00-16:00 NY: +2,19 → +3,03 pb (t 3,53), 100 % años, coste 0,79.
2. EURJPY corto el último día hábil del trimestre (Q0), 01:00-02:00 NY: −5,43 → −3,64 pb (t −3,37), 100 % años, coste 0,96.
3. HO largo el penúltimo día hábil del trimestre (Q−1), 16:00-17:00 NY: +8,20 → +8,40 pb (t 4,21), 100 % años, coste 2,5.
## Pruebas (HistData M1, BID, EST → NY; días hábiles con datos del propio par)
1. EURUSD Q+1 15:00→15:59 largo: (a) 2012-2026 (otra fuente, mismos años); (b) **2003-2011 (años nunca usados)**.
2. EURJPY Q0 01:00→01:59 corto: 2012-2026 (otra fuente).
3. HO: no hay fuente independiente de gasóleo; informativo con WTIUSD (crudo contado) Q−1 16:00→16:58 largo, 2010-2026.
Criterio de cada una: media con su signo > 0 con t (NW) ≥ 2,0 y ≥ 60 % de años con el signo (en 1b basta media > 0 con t ≥ 1,65 por ser
una prueba fuera de periodo). Lo que pase se pre-registra como estrategia (4 operaciones/año) para demo; lo que no, se descarta. Contador +4.
