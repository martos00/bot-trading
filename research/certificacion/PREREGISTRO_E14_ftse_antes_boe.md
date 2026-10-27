# PREREGISTRO E14 — FTSE largo los 2 días previos a la decisión del Banco de Inglaterra (vigilancia en vivo) — 27-oct-2026

Base: C80 (FTSE +31,5 pb de cierre D−3 a cierre D−1, t 2,31, 2015-2026; futuro ICE y Yahoo coinciden). Es una replicación del
estudio de Quantpedia (2025), no una validación posterior a su publicación. Regla del EA: largo UK100 a las 11:30 NY (≈ 16:30 de Londres;
en las semanas de desfase horario queda una hora antes o después) del 3.er día hábil antes de la decisión, salida a la misma hora 2 días
hábiles después. Tamaño y protecciones como el resto. **Desactivada por defecto.**

Criterio de activación (fijado ahora): seguimiento de las próximas decisiones con la regla congelada (en demo o en papel). Se activa solo si,
tras al menos 8 decisiones nuevas (≈ 1 año), la media neta de costes es > 0 y el coste medido (spread + 2 noches de swap) es ≤ 10 pb.
Si la media es ≤ 0, se descarta. No se cambian días ni horas.
