# PREREGISTRO C103 — Ruptura del rango europeo en índices europeos (análogo de C99 con la sesión de Europa) — 29-oct-2026

Redactado y subido a git ANTES de calcular. C99/C101/C102: el rango de una sesión, roto en la sesión siguiente, continúa en mercados
dominados por esa primera sesión (oro, Nikkei, cobre). Análogo europeo: rango de la mañana europea, roto con la apertura de EE. UU.

## Regla (hora de NY)
Rango = máximo/mínimo de 03:00 a 09:30 NY (de la apertura de Fráncfort/París/Londres a la apertura de Nueva York). Ventana de ruptura
09:30 → 13:30 NY; primera ruptura; entrada al nivel (o a la apertura del minuto si abre más allá); stop = el otro extremo del rango;
objetivo = 1 × anchura; cierre 15:55 NY (antes del cierre de Eurex a las 16:00 NY). Mismo minuto stop y objetivo → stop. Días laborables.

## Mercados (3 pruebas) y datos
DAX (GRXEUR), CAC 40 (FRXEUR), FTSE 100 (UKXGBP). Principal: HistData M1 2010-06 → 2026-09. Confirmación: QuantConnect CFD de Oanda
1 min (DE30EUR, FR40EUR, UK100GBP), hora calibrada antes contra HistData. Informativo: Euro Stoxx 50 (ETXEUR, solo hasta 2019).
Coste (futuro Eurex/ICE aprox.): DAX 1,0 pb; CAC 1,5; FTSE 1,0.

## Criterio (Bonferroni unilateral 0,05/3 → t ≥ 2,39)
Principal: media > 0 con t (Newey-West) ≥ 2,39; ≥ 60 % de años positivos; > 0 en 2010-19 y 2020-26; media > coste.
Confirmación: media > coste con t ≥ 2,0. Aviso: los futuros de Eurex/ICE no están en todas las firmas de futuros. Contador +3.
