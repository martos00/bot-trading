# PREREGISTRO C85 — Noche frente a día en futuros de metales, energía y cereales (operable en firmas de fondeo de futuros) — 28-oct-2026

Redactado y subido a git ANTES de calcular. Objetivo del usuario: ventajas para una cuenta de fondeo de FUTUROS (costes bajos; hay que
estar fuera antes de las 16:45-16:50 NY y no cruzar el cierre diario). Los barridos previos (B2-B14) eran franjas de 1 h; una deriva
repartida en muchas horas (tipo "overnight drift", Boyarchenko et al., probada solo en índices) no se habría detectado. Ambos tramos
caben en la sesión de un día de negociación (de la reapertura a las 18:00 NY hasta antes de las 16:45).

## Datos
Futuros Databento horarios (`databento/h1`, contrato del día; se descarta el tramo si cambia el contrato), 2010-06 → 2026-09,
lunes a viernes. Precio = cierre horario (índice = fin de barra, hora NY).
Metales y energía (GC, SI, PL, PA, HG, CL, HO, RB): NOCHE = cierre de 19:00 del día anterior → cierre de 09:00; DÍA = 09:00 → 16:00.
Cereales (ZC, ZS, ZW, ZL, ZM; reabren a las 20:00 NY): NOCHE = 21:00 del día anterior → 09:00; DÍA = 09:00 → 14:00.
Lunes: "día anterior" = sesión del domingo. 13 mercados × 2 tramos = 26 reglas.

## Criterio (sin signo previsto; como los barridos B)
Descubrimiento 2010-06 → 2017: se seleccionan las reglas con |t (Newey-West)| ≥ 3,0. Confirmación 2018 → 2026-09 con el signo del
descubrimiento: t ≥ Bonferroni unilateral 0,05/k_sel, ≥ 60 % de años con el signo y media ≥ 3 × coste del futuro (costes de B4/B5).
Lo que pase necesita otra fuente (HistData XAU/XAG/WTI donde exista) antes de nada. Contador +26.
