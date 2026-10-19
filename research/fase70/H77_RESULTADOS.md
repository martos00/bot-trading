# H77 — Oro largo en sesión de Tokio (09:00 → 15:00 JST): RESULTADOS

Reglas y criterios congelados en `PREREGISTRO_H77_oro_asia.md` (commit previo a cualquier cálculo).
Datos: HistData XAUUSD M1 2009-2026 (zona NY con horario de verano, verificada); `calidad_datos`: VÁLIDO;
días en huecos excluidos. Motor: `h77_oro_asia.py m1`.

## Bruto (BID M1, sin costes), rentabilidad logarítmica por día
| Tramo | Regla: n / media / t / SR anual | Control +12 h: media / t | Regla − control: media / t |
|---|---|---|---|
| IS 2009-2019 | 2632 / **+2,34 pb** / **3,31** / 1,02 | +0,21 pb / 0,16 | +2,07 pb / 1,37 |
| OOS 2020-2026 | 1594 / **+0,27 pb** / **0,21** / 0,08 | −1,40 pb / −0,73 | +1,48 pb / 0,66 |

Por años (pb/día, regla): 2020 −3,9 · 2021 +5,8 · 2022 −1,9 · 2023 +0,4 · 2024 +1,2 · 2025 +4,0 · 2026 −4,8
→ positiva en 4 de 7 años OOS. En $/oz la media OOS es −0,037 $ (antes de costes).

## Veredicto: RECHAZADA
El efecto "sombrero" de Donati & Jung se reproduce en su período (IS t = 3,3), pero **desaparece después**
(OOS bruto t = 0,21, frente a t ≥ 3 exigido; 4/7 años frente a ≥ 5). Los costes ejecutables (spread
≈ 1 pb + 0,4 pb de deslizamiento) solo pueden empeorarlo, así que la descarga de ticks se detuvo en 2020-05
por innecesaria: **no cambia el veredicto y no se ha modificado ninguna regla**. No hay simulación de fondeo.
Es otro caso de decaimiento tras la publicación (McLean-Pontiff). N acumulado = 92.
