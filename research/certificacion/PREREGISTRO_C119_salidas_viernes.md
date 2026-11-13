# PREREGISTRO C119 — Salida anticipada en el oro y la plata del viernes (objetivo o stop que sigue al pico)

Redactado y subido a git ANTES de calcular (13-nov-2026). Motivo: en Apex Intraday la pérdida máxima sigue el pico en tiempo real y los
viernes suelen devolver parte de lo ganado. Pregunta: ¿salir antes de la hora (en el pico) mejora el resultado?

Datos: futuros GC (16:00→16:55 NY) y SI (16:30→16:57 NY), velas de 1 minuto, viernes 2010-2026 (los mismos de apex_examen_minuto.py).
σ = desviación de la franja en los 52 viernes anteriores. Coste: GC 0,74 pb, SI 2,3 pb (ida y vuelta).

## Parte descriptiva (no decide)
Pico favorable máximo (MFE) dentro de la franja, en σ; cuánto se devuelve del pico al cierre; % de operaciones que acaban por debajo de
la mitad de su pico.

## Reglas candidatas (6, cerradas aquí)
- T1, T1.5, T2: objetivo fijo a +1, +1,5, +2 σ (si no se toca, salida a la hora normal).
- R1, R2, R3: stop que sigue al pico: se activa al ganar +1 σ y cierra si devuelve 0,5 / 0,75 / 1 σ desde el pico (si no, salida normal).
Todas mantienen el stop de catástrofe de 2 σ.

## Procedimiento
1. Con 2010-2017 (dentro de muestra) se elige la regla con mayor resultado medio por operación (en σ), por mercado. Si ninguna supera a
   la salida normal, se acaba aquí: no hay regla.
2. Esa única regla se prueba en 2018-2026 (fuera de muestra). Pasa si mejora el resultado medio por operación frente a la salida normal
   en 2018-2026 con t ≥ 1,65 (diferencia emparejada por viernes) y no empeora la peor racha de 10 viernes.
3. No se prueban más reglas ni otros parámetros después de ver 2018-2026.
