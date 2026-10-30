# C104 y C105 — Resultados: barrido del máximo/mínimo de ayer y retrocesos de Fibonacci (vídeos de TikTok) — 30-oct-2026
Preregistro commit 2e2fb6d. Scripts `c104_barrido_pdh.py`, `c105_fibonacci.py`; salidas `c104_resultados.txt`, `c105_resultados.txt`.

## C104 — Barrido PDH/PDL con vela de confirmación (velas de 15 min, 2010-2026): NO PASA en ningún mercado
| Mercado | n | Media | t | Acierto | R medio |
|---|---|---|---|---|---|
| Oro | 609 | +0,32 pb | 0,20 | 14 % | +0,02 |
| EURUSD | 667 | −0,21 | −0,26 | 15 % | −0,01 |
| USDJPY | 477 | −0,27 | −0,28 | 13 % | −0,04 |
| GBPUSD | 669 | −0,26 | −0,29 | 18 % | +0,07 |
| S&P 500 (ES) | 576 | −3,07 | −1,50 | 18 % | −0,06 |
El objetivo (mínimo de ayer) se alcanza solo el 13-18 % de las veces; el resultado es cero antes de costes y negativo después.
Coherente con C93: en el oro, romper el máximo de ayer tiende a CONTINUAR, no a girarse.

## C105 — Fibonacci (velas diarias, 10 mercados)
- Niveles de Fibonacci frente a niveles de control: +3,1 pb (t ≈ 0,24); llegar al objetivo 44,2 % (Fibonacci) frente a 47,4 % (control).
  **Los niveles de Fibonacci no son especiales.**
- Estrategia (compra/venta en 38,2/50/61,8 con vela de confirmación): n 2.080, −7,23 pb (t −1,42); 2010-17 −2,30; 2018-26 −11,08. **NO PASA.**
Contador +7.
