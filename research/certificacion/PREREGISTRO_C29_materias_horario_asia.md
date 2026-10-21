# Pre-registro C29 — Materias primas que importa China en horario de Shanghái (21-oct-2026)

Redactado y enviado a git ANTES de descargar los datos horarios y de calcular nada.
Mecanismo (el mismo que el de la única ventaja certificada, E1): los compradores locales cubren/compran en su horario.
China es el mayor importador de cobre, soja, crudo y oro; sus importadores y fabricantes operan en horario de Shanghái.
Previsión: el precio SUBE en la sesión asiática.

## Regla
Largo de 01:00 a 07:00 UTC (09:00-15:00 hora de Pekín, sin horario de verano) cada día laborable, en cobre (HG), soja (ZS),
crudo WTI (CL) y oro (GC). Barras horarias de Databento, contrato continuo por volumen, sin rentabilidades entre contratos.
Nota: las sesiones de grano del CME (ZS) cierran parte de la noche; se usa lo que haya entre esas horas (si no hay barra en
alguno de los extremos, ese día no cuenta).
**Prueba principal: factor = media de los cuatro.** Pares por separado: informativos (Holm, 4).

## Tramos y criterios
Descubrimiento 2010-06 → 2017: media > 0. Confirmación 2018 → 2026-09: (1) media > 0 con t de Newey-West ≥ 2,0;
(2) ≥ 60% de años positivos; (3) neta de un coste de futuros de 1 tick por ida y vuelta (HG 1,1 pb, ZS 2 pb, CL 1,5 pb,
GC 0,5 pb) > 0 y bruta ≥ 3 × coste. Informativo: misma ventana en sentido contrario (horario de EE. UU.), correlación con E1.
Contador +1 (N ≈ 1.201).
