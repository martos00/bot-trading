# C76 — Resultados: continuación 5 minutos después de noticias — 27-oct-2026
Reglas congeladas en PREREGISTRO_C76 (commit 654ecb7). Script `c76_continuacion_noticias.py`, salida `c76_resultados.txt`.
Fechas NFP identificadas con el ES: 195, 97 % viernes; comprobadas a mano 2019-2020 (p. ej. 2020-01-10 y 2020-07-02, correctas).

| Evento | Mercado | n | Continuación (pb) | t | 1.ª mitad | 2.ª mitad | Veredicto |
|---|---|---|---|---|---|---|---|
| FOMC comunicado 14:00 | oro | 108 | +5,41 | 1,69 | +9,86 | +0,78 | NO PASA |
| FOMC comunicado 14:00 | EURUSD | 104 | +0,88 | 1,00 | +0,45 | +1,36 | NO PASA |
| Rueda de prensa 14:30 | oro | 61 | −16,10 | −2,34 | −24,22 | −7,72 | NO PASA (signo contrario) |
| Rueda de prensa 14:30 | EURUSD | 56 | −6,72 | −2,02 | −7,44 | −5,89 | NO PASA (signo contrario) |
| Empleo NFP 08:30 | oro | 188 | −3,08 | −1,17 | −4,68 | −0,78 | NO PASA |
| Empleo NFP 08:30 | EURUSD | 188 | −2,10 | −1,60 | −0,52 | −4,47 | NO PASA |

- **Ninguna continuación pasa.** El comunicado del FOMC en oro fue positivo hasta 2019 y casi nulo desde 2020 (menor que el coste).
- **Hallazgo informativo, no certificado**: tras la **rueda de prensa** el primer movimiento tiende a **revertirse** en los dos
  mercados y en las dos mitades (oro +16 pb, EURUSD +6,7 pb en reversión, |t| ≈ 2-2,3, n ≈ 60). No era la hipótesis
  preregistrada y la muestra es pequeña: solo podría tratarse como candidata con un preregistro nuevo y confirmación en
  otros mercados/fuentes. Contador +6.


## Corrección 27-oct-2026 (hora de HistData)
Repetido con la hora de HistData corregida (`c76_resultados.txt`). Cambia EURUSD: comunicado del FOMC **+4,13 pb (t 3,05)**, >0 en ambas mitades, 2.ª mitad +2,82 pb → pasaba en HistData. **Segunda fuente FXCM (punto medio, `c76b_resultados.txt`): +2,84 pb (t 1,92), desde 2020 +0,60 pb < coste 1,1 → NO CONFIRMA.** Rueda de prensa EURUSD: −5,85 pb (t −1,48). NFP EURUSD: −1,54 pb. Oro sin cambios. Resultado final de C76: **ninguna certificada**.
