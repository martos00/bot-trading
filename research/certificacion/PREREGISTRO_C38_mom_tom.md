# Pre-registro C38 — Efecto MOM-TOM: el trend following gana en el cambio de mes (Van Hemert 2014) — 21-oct-2026
Redactado y enviado a git ANTES de calcular nada con estos datos (curva c.0/c.1 de 16 materias primas descargada para C34,
todavía incompleta y sin usar para esto).
## Fuente (resúmenes de CXO Advisory y Quantpedia; texto completo no leído)
Van Hemert, "The MOM-TOM Effect: Detecting the Market Impact of CTA Trading" (SSRN 2515900, 2014): el 90 % del rendimiento
acumulado del Newedge Trend Index 2000-2014 se obtuvo en los días de cambio de mes (TOM = 2 últimos días hábiles + 1.º del
mes siguiente). Más fuerte en materias primas poco líquidas. Mecanismo: las entradas de dinero de fin de mes a los CTA
amplían posiciones de tendencia y empujan el precio a su favor. Contrapunto: Baltas-Kosowski no ven relación flujo-retorno.
## Regla
Universo: 16 futuros de C34 (CL HO RB NG GC SI HG PL ZC ZS ZW ZL ZM KE LE HE), c.0 diario, sin rentabilidades entre contratos.
Señal de cada mercado al cierre del antepenúltimo día hábil del mes: signo de la suma de rentabilidades diarias válidas de
los 252 días anteriores. Tamaño: 1 / (volatilidad de 60 días), normalizado para que la cartera tenga igual riesgo por mercado
(peso_i = (1/σ_i) / Σ(1/σ_j)). Posición mantenida durante las rentabilidades de los 2 últimos días hábiles del mes y del 1.º
del siguiente. Coste: 3 pb por lado y mercado (6 pb ida y vuelta, ponderado).
Informativo (no decide): la misma cartera en los días no-TOM y la diferencia TOM − no-TOM por día.
## Tramos y criterios
Descubrimiento 2011-2014 (dentro de la muestra del autor). **Confirmación 2015-01 – 2026-09**: media mensual neta > 0 con
t (Newey-West, 3) ≥ 2,0 y ≥ 60 % de años positivos. Sin cambiar ventana, señal ni universo tras ver datos. Contador +1.
Aplicabilidad: mantiene 3 días (cuenta Swing de FTMO o futuros); CFD de petróleo, gas, oro, plata, cobre y grano existen.
