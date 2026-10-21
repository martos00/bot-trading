# Resultados B2 — Barrido de franjas horarias en 15 futuros del CME (Databento): NINGUNA NUEVA CERTIFICADA

Pre-registro `PREREGISTRO_B2_barrido_horario_futuros.md`; script `b2_barrido_futuros.py`; salida `b2_resultados.txt`,
tabla completa `b2_todas.csv`. Datos ≈ 7,5 $ del crédito gratuito (más los ya descargados).

- Reglas evaluadas: 584 (algunas franjas sin datos suficientes en grano). Seleccionadas en 2010-2017 (|t| ≥ 3): 46.
  Umbral de Bonferroni en 2018-2026: t ≥ 3,07.
- **Control superado:** la franja 06:00-08:00 NY del futuro del euro (6E) aparece sola: −1,71 pb (t −4,55) en 2010-2017 y
  −1,32 pb (t −4,48) en 2018-2026, 78% de años. El método encuentra la ventaja ya certificada (E1). Con el coste de 1 tick
  del futuro (0,75 pb) no llega a 3× (1,8×): consistente con lo que ya sabíamos (E1 es operable con costes bajos).
- **Ninguna franja nueva pasa todos los criterios.** Las más cercanas (informativas, no certificadas):
  | Franja | 2018-2026 | Por qué no pasa |
  |---|---|---|
  | Oro 16:00-17:00 NY, largo | +0,85 pb (t 3,09), 89% años | Bruto/coste 1,2× (coste 0,74 pb) |
  | Nasdaq 01:00-03:00 NY, largo | +1,34 pb (t 2,55), 89% años | t < 3,07 (bruto/coste 4,5×) |
  | Plata 16:00-17:00, largo / 06:00-07:00, corto | +1,6 / +2,1 pb (t 2,9) | Coste 2,3 pb |
  | Cobre 12:00-13:00, largo | +2,2 pb (t 2,51) | t y coste |
  El Nasdaq de madrugada (01:00-03:00 NY, apertura europea) es el antiguo "overnight drift" (Boyarchenko et al.), que
  sigue positivo con datos limpios; queda como candidata para vigilar.
Contador +584 (N ≈ 1.788).
