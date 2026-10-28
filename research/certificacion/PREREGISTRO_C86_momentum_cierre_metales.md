# PREREGISTRO C86 — Momentum de la última media hora antes de la liquidación (Baltussen, Da, Lammers y Martens, JFE 2021) en oro y plata — 28-oct-2026

Redactado y subido a git ANTES de calcular. Propuesto como prioridad 1 (vía ChatGPT). Ya probado en S&P y Nasdaq (H69: el efecto
existía en 2010-2013 y desaparece tras publicarse; C11 condicionado a gamma: no significativo). Nunca en metales con costes de futuros.

## Regla (futuros Databento 1 minuto, contrato del día)
- Oro GC: liquidación 13:30 NY. Señal = signo de ln(P 13:00 / P liquidación del día hábil anterior (13:30)). Posición en ese sentido de
  13:00 a 13:30.
- Plata SI: liquidación 13:25 NY. Señal = signo de ln(P 12:55 / P 13:25 del día anterior). Posición de 12:55 a 13:25.
Precio = cierre del último minuto anterior a cada hora (hasta 10 min atrás). Sin cambio de contrato entre las tres horas.

## Criterio (2 pruebas, signo previsto: continuación)
Media > 0 con t (Newey-West) ≥ 1,96 (Bonferroni unilateral 0,05/2) en 2010-2026; > 0 en 2010-2017 y en 2018-2026; **2021-2026
(tras la publicación) > coste del futuro** (GC 0,74 pb, SI 2,3 pb); ≥ 60 % de años positivos. Lo que pase → otra fuente (HistData) y
plan de ejecución en firma de futuros. Contador +2.
