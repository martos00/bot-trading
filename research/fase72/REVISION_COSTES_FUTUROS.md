# ¿Cambia algo operar índices con micro-futuros (cuenta de fondeo de futuros)? (20-oct-2026)

Revisión de todas las pruebas intradía de índices del proyecto (README y fases 69-72) buscando ventajas brutas
significativas que los costes de CFD hubieran eliminado. Es una re-evaluación de datos ya vistos: **informativa,
no confirmatoria**.

## Hallazgo principal: los micro-futuros no son mucho más baratos que lo ya supuesto
- Nasdaq: CFD supuesto en H76 = 1,5 puntos (≈ 0,7-1 pb); MNQ = 0,75 pt de comisión (1,50 $/contrato) + 1 tick de
  entrada ≈ 1,0 pt, más 1 tick en la salida por stop. Casi igual.
- S&P: H69 ya suponía ≈ 1,6 pb; MES ≈ 0,7-1,5 pb. H79 y H80 ya usaban costes de micro-futuros.
- Solo Noise Area (H74) mejoraba de verdad con costes de MES (SR 1,03 → 0,43 en lugar de ≈ 0 con CFD).

## Candidatas revisadas
| Estrategia | Resultado con costes de micro-futuros | Conclusión |
|---|---|---|
| H76 ORB 5 min, NDX (MNQ: 1,0 pt + 0,25 pt en stops) | 2010-15: bruto +0,023R, neto −0,249R (t −3,45). 2016-feb 2023: bruto +0,187R (t 3,01), neto +0,092R (t 1,48). **Post-publicación mar-2023 → 2026: bruto +0,147R (t 1,64), neto +0,118R (t 1,32), n = 735** | No significativa (el pre-registro de H76 exigía t ≥ 2) |
| H74 Noise Area SPY/ES | No hay datos gratuitos de SPY con volumen posteriores a may-2021 (el conjunto de Kaggle "actualizado" en 2025 es el mismo). Réplicas independientes: SPY 2025 −4,9%, 2026 −12,9%; ES 2024-05 → 2026-07 SR −0,07 antes de costes | Sigue descartada: el problema es la señal, no el coste |
| H69 momentum intradía | Solo fue significativa en bruto en 2010-13; desde 2020 ≈ 0 en bruto | Descartada |
| H79, H80 (índices) | Ya evaluadas con costes de micro-futuros | Descartadas |

## Conclusión
Pasar a una cuenta de fondeo de futuros no convierte ninguna prueba previa en candidata. Lo más cercano es el ORB de
5 minutos en MNQ (+0,118R neto post-publicación, t = 1,32): compatible con una ventaja pequeña, pero también con el azar.
