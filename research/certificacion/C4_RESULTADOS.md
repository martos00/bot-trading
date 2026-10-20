# C4 — Factor "dólar débil en horario de EE. UU.": RESULTADOS (20-oct-2026)

Pre-registro: `PREREGISTRO_C4_dolar_horario_eeuu.md` (commit c4bde2b, antes de descargar). Salida: `c4_resultados.txt`.
HistData M1 2003-2011; huecos de la auditoría excluidos (EUR/USD ago-2003, 4 días; USD/CHF mar-2004, 9 días).

| Periodo | Factor (EUR/USD +, GBP/USD +, USD/CHF −) | Criterio | |
|---|---|---|---|
| **2008-2011 (principal, fuera de la muestra del estudio)** | +1,64 pb/día, **t = 1,01** | t ≥ 1,645 | **No cumple** |
| 2003-2011 (secundario) | +2,87 pb/día, t = 2,99, 7/9 años positivos | t ≥ 2 y ≥ 6/9 | Cumple |

Por par: 2003-2007 los tres con t 3,3-3,6 (es el período del estudio original); 2008-2011 EUR/USD +0,35 (t 0,19), GBP/USD
+1,75 (t 0,96), USD/CHF +2,53 (t 1,34). USD/JPY (informativo): +1,28 (t 1,28) y +0,15 (t 0,10).
Por año: 2003 +9,6 · 2004 +3,1 · 2005 +0,1 · 2006 +5,0 · 2007 +2,2 · 2008 −0,3 · 2009 +6,0 · 2010 +1,1 · 2011 −0,3.

## Veredicto: NO CERTIFICADA
Falla el criterio principal. Era una prueba de poca potencia (t esperada ≈ 1,3 si el efecto era como en 2012-2026), así que
el resultado no demuestra que el efecto sea falso: el signo es el previsto en todos los períodos (2003-2007 fuerte, 2008-2011
débil, 2012-2026 moderado, Sharpe ≈ 0,67). Pero no cumple el estándar fijado y **no entra en la cartera**. La única forma de
resolverlo sin reutilizar datos es acumular datos nuevos (forward).
