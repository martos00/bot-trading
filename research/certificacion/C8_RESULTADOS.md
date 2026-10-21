# Resultados C8 — Ciclo de subastas del Tesoro (Lou-Yan-Zhang 2013): pasa el pre-registro con el proxy, NO OPERABLE hoy

Pre-registro: `PREREGISTRO_C8_subastas_tesoro.md` (commit c19cc90). Script `c8_subastas_tesoro.py`, salida `c8_resultados.txt`.

## Prueba pre-registrada (nota a 5 años, precio aproximado con el rendimiento DGS5 de FRED)
| | Réplica 1990-jun 2008 | Confirmación jul 2008-2026 |
|---|---|---|
| Ciclo (corto 5 días antes + largo 5 días después), bruto | 22,2 pb, t 3,42 (paper: 22,5) | 20,9 pb, t 3,79 |
| Neto (coste 2,36 pb) | 19,8 pb, t 3,05 | 18,6 pb, t 3,36 |
| Bruto/coste · años netos + | 9,4 · 14/18 | 8,9 · 15/19 |
Los cuatro criterios se cumplen. La réplica reproduce casi exactamente la cifra del paper.

## Comprobaciones con el futuro real ZF (Yahoo ZF=F, cierres diarios; días de cambio de contrato anulados) — no pre-registradas, decisivas
| Nota a 5 años | Rendimiento DGS5 | Futuro ZF |
|---|---|---|
| Confirmación jul 2008-2026 | 20,9 pb, t 3,79 | **10,5 pb, t 2,10** |
| 2008-2013 | 50,9 pb, t 4,38 | 27,0 pb, t 2,43 |
| **2014-2026 (tras la publicación)** | 8,0 pb, t 1,37 | **3,3 pb, t 0,64** |
Correlación ciclo a ciclo entre las dos series: 0,93. Con el futuro, que es lo que se opera, el efecto es la mitad, y desde
2014 es de 3,3 pb frente a 2,4 pb de coste (1,4 veces), sin significación. Lo mismo en 2 años (ZT 2014-2026: 3,2 pb, t 1,74,
coste 1,2 pb) y 10 años (ZN 2014-2026: 2,0 pb, t 0,25).

## Conclusión
El efecto fue real y grande hasta 2013 (sobre todo 2008-2011) y casi ha desaparecido tras publicarse (McLean-Pontiff otra
vez). **No se certifica para operar.** Única pista restante: ZT (2 años) 2014-2026, 3,2 pb, t 1,74, 2,7 veces el coste;
no llega a ningún umbral y elegirla ahora sería selección a posteriori: solo como forward test si se pre-registra.
