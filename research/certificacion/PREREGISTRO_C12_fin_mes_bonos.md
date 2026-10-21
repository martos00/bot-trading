# Pre-registro C12 — Fin de mes en los bonos del Tesoro (Hartley y Schwarz 2019) con futuros (21-oct-2026)

Redactado y enviado a git ANTES de calcular ningún resultado.

## Fuente (resumen de CXO Advisory; no he leído el artículo original)
Hartley y Schwarz (2019), "Predictable End-of-Month Treasury Returns": con bonos cupón cero modelados a 2, 5 y 10 años
(1990-2018), la mayor rentabilidad en exceso aparece el **último día hábil del mes**; menor pero significativa el penúltimo.
Más débil en 2015-2018. Mecanismo: rebalanceo de los índices de bonos el último día del mes (entran las emisiones nuevas,
sube la duración del índice) y maquillaje de carteras; los fondos indexados compran duración ese día. Se extiende a futuros.

## Regla
Largo del futuro del bono a 10 años (ZN) del cierre del penúltimo día hábil del mes al cierre del último (1 sesión).
Datos: Yahoo `ZN=F` (cierres diarios, contrato continuo); los días de cambio de contrato (|rentabilidad| > 5 desviaciones
típicas de 60 días) se anulan, como en C8. Informativo: ZF (5 años) y ZB (30 años); dos últimos días; resto de días.

## Costes (futuros)
1 tick de ZN (15,625 $) + 4 $ de comisión por ida y vuelta sobre ≈ 110.000 $ de nominal ≈ 1,8 pb.

## Tramos y criterios (ZN)
- Réplica 2001-2018 (dentro del período del estudio): media bruta > 0.
- **Confirmación 2019 → 2026-09** (después del estudio), todos: (1) media neta > 0 con t ≥ 2,0; (2) media bruta ≥ 3 × coste;
  (3) neta positiva en ≥ 60% de los años; (4) mayor que la media del resto de días (t de la diferencia ≥ 1,645).
Aviso de potencia: ≈ 93 meses en confirmación; con una desviación diaria de ≈ 35 pb, t ≥ 2 exige ≈ 7 pb de media.
Contador +1 (N ≈ 1.164). Si falla, se descarta sin cambiar el día ni el plazo.
