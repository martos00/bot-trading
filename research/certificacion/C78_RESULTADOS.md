# C78 — Candidatas reaparecidas en la auditoría de la hora de HistData: segunda fuente — 27-oct-2026

## 1. EURUSD largo el 1.er día hábil del trimestre (Q+1), 15:00 → 16:00 NY
| Fuente | Periodo | n | Media | t | Años + |
|---|---|---|---|---|---|
| Futuro 6E (B13, descubrimiento) | 2010-2026 | ~60 | +2,19 → +3,03 pb | 3,53 | 100 % |
| HistData (C54 1a, hora corregida) | 2012-2026 | 48 | +2,33 pb | 4,91 | 13/15 |
| **FXCM punto medio (C78, `c78_resultados.txt`)** | 2012-2026 | 54 | **+2,41 pb** | **4,15** | **14/15** |
| HistData fuera de periodo (C54 1b, hora corregida) | 2003-2011 | 29 | −0,02 pb | −0,01 | 4/9 |
Tres fuentes coinciden desde 2010-2012, pero **no existía en 2003-2011**, y C54 exigía también ese tramo (t ≥ 1,65). Según las reglas
preregistradas **NO se certifica**. Queda como candidata "reciente" (efecto que aparece hacia 2010). Neto con coste FTMO (0,54 pb) ≈ +1,9 pb,
4 operaciones al año: aportaría muy poco a la cartera.

## 2. Nikkei largo el 2.º día hábil del trimestre (Q+2), 15:00 → 16:00 NY
| Fuente | n | Media | t | Años + |
|---|---|---|---|---|
| Futuro NKD (B14, descubrimiento) | 57 | 2010-17 +24,5 pb; 2018-26 +12,0 pb | 3,78 / 4,87 | 89 % |
| **CFD JPXJPY de HistData (C60, hora corregida)** | 60 | **+16,2 pb** | **4,12** | **15/16**; 2018-26 +10,7 (t 3,65) |
Con la hora correcta **PASA el criterio de C60** (t ≥ 2, ≥ 60 % de años). La explicación de "precio rancio del NKD" ya no se sostiene: el CFD
lo reproduce. Aviso: el CFD probablemente cotiza a partir de los futuros a esa hora, así que no es una fuente totalmente independiente; no
hay una tercera fuente gratuita accesible (Dukascopy bloquea esta sesión). Siguiente paso: medir el coste del JP225.cash de FTMO a esa
hora y preregistrar la estrategia (4 operaciones al año) antes de añadirla al bot.
