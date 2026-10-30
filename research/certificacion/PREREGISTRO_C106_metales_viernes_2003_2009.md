# PREREGISTRO C106 — Oro y plata del viernes en 2003-2009 con Dukascopy (datos nunca usados en el proyecto) — 30-oct-2026

Redactado y subido a git ANTES de tener los datos. Objetivo: confirmar fuera de muestra (antes de 2010, otro proveedor, precio medio
bid/ask) la pieza principal de la cartera: los metales suben el viernes al final de la sesión (E8 oro, plata viernes; mecanismo de
C50: cobertura antes del cierre largo). Todas las pruebas previas usan 2010-2026.

## Datos (descarga del usuario en su ordenador; aquí Dukascopy bloquea con 429)
Dukascopy XAUUSD y XAGUSD, velas de 5 minutos, BID y ASK por separado, 2003-05 → 2009-12, hora UTC. Precio = (bid + ask) / 2 al
cierre de la vela. Conversión a hora de Nueva York con cambio de hora (reglas de EE. UU. de cada año, incluida la de 2007).

## Reglas (idénticas a las de la cartera; no se cambia nada)
- **Oro viernes:** largo del cierre de la vela que termina a las 16:00 NY al cierre de la que termina a las 16:55 NY. Viernes que no son
  festivo NYSE.
- **Plata viernes:** largo de 16:30 a 16:55 NY (16:55 es la última vela de 5 min completa antes de la salida a las 16:57 del bot).
- Informativo: plata víspera de festivo 16:00-16:55; oro y plata de lunes a jueves a la misma hora (placebo); spread medio a esas horas.

## Criterio (2 pruebas; Bonferroni unilateral 0,05/2 → t ≥ 2,24)
Para cada metal: media > 0 con t (Newey-West) ≥ 2,24 y ≥ 60 % de años positivos (2003-2009, 7 años). Placebo lunes-jueves sin efecto
(|t| < 2). Pasa → la ventaja se considera confirmada en un periodo y proveedor independientes. Contador +2.
