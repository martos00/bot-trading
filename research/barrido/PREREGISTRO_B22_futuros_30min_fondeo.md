# PREREGISTRO B22 — Barrido calendario × 30 min en 23 futuros del CME, solo ventanas operables en cuentas de fondeo de futuros — 28-oct-2026

Redactado y subido a git ANTES de calcular. Objetivo del usuario: ventajas para una cuenta de fondeo de FUTUROS (no CFD). Datos de
QuantConnect (AlgoSeek, futuros 1 minuto con sesión nocturna; continuo por interés abierto, ajuste "backwards ratio" para que el
cambio de contrato no cree saltos). El cálculo se hace dentro de QuantConnect; solo se exportan estadísticas resumidas (límite de 10 KB).

## Por qué es nuevo
Los barridos anteriores eran de 1 h en ~30 futuros (B2-B14) o de 30 min solo en oro, plata y S&P (B18). Con costes de futuros, efectos
de 30 min pequeños pueden ser operables. Se limita a lo que permite una firma de fondeo de futuros: ventanas dentro de la sesión
(inicio 18:00 → fin como muy tarde 16:30 NY), sin cruzar el cierre diario.

## Universo y costes de ida y vuelta (pb; tick + comisión, como B4/B5)
ES 0,73 · NQ 0,30 · RTY 1,2 · YM 0,8 · CL 2,0 · NG 4,7 · HO 2,5 · RB 3,0 · GC 0,74 · SI 2,3 · HG 1,65 · PL 3,5 · 6E 0,75 · 6J 1,2 ·
6B 1,3 · 6A 1,3 · 6C 1,4 · ZN 1,8 · ZB 2,7 · ZF 1,5 · ZC 6,6 · ZS 2,5 · ZW 4,5. (23 mercados)

## Reglas
- Franjas de 30 min con inicio en cada :00 y :30 desde las 18:00 hasta las 16:00 NY (fin ≤ 16:30), excepto las que crucen 17:00-18:00.
  Precio = cierre del último minuto anterior al inicio y al fin (hasta 10 min atrás); sin precio, sin dato. Rentabilidad logarítmica.
  La sesión que empieza a las 18:00 se asigna al día de negociación siguiente.
- Tipos de día (día de negociación, lunes a viernes): lunes, martes, miércoles, jueves, viernes; D−2, D−1, D0, D+1, D+2 (posición en el
  mes, días con datos del propio mercado); PRE y POST (víspera y día después de festivo NYSE). 12 tipos.
- Total ≈ 23 × 44 × 12 ≈ 12.000 reglas.

## Criterios (como B4/B7, más estrictos por el número de reglas)
- Descubrimiento 2012-01 → 2017-12: selección |t (Newey-West, 5 retardos)| ≥ 4,0 con n ≥ 250 (días de la semana) o n ≥ 50 (resto).
- Confirmación 2018-01 → 2026-09 con el signo del descubrimiento: t ≥ Bonferroni unilateral 0,05/k_sel; ≥ 60 % de años con el signo;
  media bruta ≥ 2 × coste.
- Lo que pase: segunda fuente (HistData o Databento ya descargado) y comprobación del mecanismo antes de nada. Contador +≈12.000.
- Si un mercado no tiene datos desde 2012 en QuantConnect, se usa lo que haya y se informa.

## Anexo (28-oct-2026, antes de calcular el barrido; correcciones de datos)
Calibración de la hora de QuantConnect contra Databento (cierres horarios de 2016-01-27 y 2022-07-27, y 6J en 2015 y 2023): ES, NQ, RTY,
YM, CL, NG, HO, RB, GC, SI y HG coinciden exactamente; **6E, 6J, 6B, 6A, 6C, ZN, ZB, ZF, ZC, ZS y ZW vienen con 1 h de adelanto** (su
marca "h" es la hora h+1 real) y se corrigen sumando 1 h. **PL se excluye**: datos muy incompletos en QuantConnect (correlación horaria
0,63-0,85 con Databento). Universo final: 22 mercados. Validación previa obligatoria: con la hora corregida, 6J D−2 07:00-08:00 debe
reproducir el signo de E9/B7 (negativo). Antes de este anexo solo se ejecutaron las pruebas de ES y 6J sin corregir (descartadas).
