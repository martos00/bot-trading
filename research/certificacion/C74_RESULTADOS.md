# C74 — Resultados: modelo "TJR" de sesión de NY (barrida Asia/Londres → MSS 5 min → FVG, 2R) — 26-oct-2026
Reglas congeladas en PREREGISTRO_C74 (commit 8e56287). Script `c74_modelo_tjr_ny.py`, salida `c74_resultados.txt`.

| Mercado | Operaciones | Aciertos | Bruto (R) | Neto (R) | t neto | 2011-18 | 2019-26 | Veredicto |
|---|---|---|---|---|---|---|---|---|
| ES (Databento) | 106 | 38,7 % | −0,111 | −0,155 | −1,75 | −0,019 | −0,258 | NO PASA |
| EURUSD (HistData) | 32 | 43,8 % | −0,044 | −0,088 | −0,63 | −0,008 | −0,158 | NO PASA |
| XAUUSD (HistData) | 67 | 50,7 % | −0,123 | −0,181 | −2,02 | −0,230 | −0,122 | NO PASA |

- Negativa **antes de costes** en los tres mercados y en ambas mitades (salvo ≈0 en ES/EURUSD 2011-18); cortos y largos
  igual de malos. No hay ningún indicio de ventaja que una segunda fuente pudiera confirmar.
- Pocas operaciones (2-7 al año): las reglas son estrictas. Embudo comprobado en EURUSD 2014-17: la mayoría de días
  no hay barrida porque los niveles de Asia/Londres ya se han tomado antes de las 09:30 (regla 1). Es consecuencia de
  las reglas preregistradas, no un error del código. Potencia baja, pero el signo es negativo en todo.
- **Cerrada.** No se prueban variantes de esta regla sobre estos datos (sería buscar hasta que algo salga por azar).
  Contador de pruebas +3.
