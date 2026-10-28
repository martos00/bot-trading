# B22 — Resultados: calendario × 30 min en 22 futuros (ventanas operables en fondeo de futuros, QuantConnect) — 28-oct-2026
Reglas en PREREGISTRO_B22 (+ anexo de calibración horaria). Código ejecutado en QuantConnect: `b22_quantconnect_plantilla.py`
(se sustituyen mercado y desfase); salida `b22_resultados.txt`. 11.220 reglas (19 mercados × 528 + 3 cereales × 396). RTY desde
2017-07 y GC desde 2012-10 en QuantConnect.

Seleccionadas en el descubrimiento 2012-2017 (|t| ≥ 4): **6** → umbral de confirmación t ≥ 2,39.

| Regla | Descubrimiento | Confirmación 2018-2026 | Veredicto |
|---|---|---|---|
| NQ viernes 02:00-02:30 | +1,91 pb (t 4,05) | +0,18 (t 0,28) | no |
| NG viernes 07:00-07:30 | −8,88 (t −4,86) | −1,70 (t 0,74 con signo) | no |
| 6E último día del mes 01:30-02:00 | −1,59 (t −4,17) | +0,59 (en contra) | no |
| 6J último día del mes 21:00-21:30 | +2,56 (t 4,31) | +1,38 (t 1,44) | no |
| 6A primer día del mes 14:30-15:00 | −2,89 (t −5,31) | +0,48 (en contra) | no |
| ZW víspera de festivo 03:30-04:00 | +6,43 (t 4,16) | +1,09 (t 0,48) | no |

**Ninguna regla pasa.** Las 6 que destacaban en 2012-2017 se apagan o se invierten en 2018-2026 (lo esperable entre 11.220 reglas: falsos
positivos). Con ventanas de 30 min y costes de futuros, el calendario de 22 futuros del CME no da nada nuevo para fondeo de futuros.
Contador +11.220.
