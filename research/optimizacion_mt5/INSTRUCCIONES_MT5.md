# Qué tienes que hacer en MetaTrader 5

Archivos: `research/optimizacion_mt5/CAND1…CAND6_*.set` (6 candidatas). No hace falta abrir cuentas ni dinero real:
el Probador funciona con la cuenta demo de MetaQuotes.

## Paso 0 — Recuperar la configuración original exacta y reproducir (lo primero)
Para cada candidata (informe y número de pasada en la tabla de abajo):
1. Probador de estrategias → abre los resultados de esa optimización (pestaña **Optimización / Resultados**; si ya no la
   tienes abierta, vuelve a lanzar la misma optimización con las mismas fechas y MT5 cargará los resultados de su caché
   sin recalcular).
2. **Doble clic en la pasada** → MT5 pone en la pestaña **Parámetros** todos los valores con que se ejecutó (incluidos
   los fijos, como `InpRiskPercent` e `InpFixedRR`).
3. En **Parámetros**: clic derecho → **Guardar** → guárdalo como `ORIGINAL_CANDx.set` y **súbemelo**.
4. Ejecuta esa prueba sin optimización (2025.01.02 – 2026.09.21) y apunta operaciones, PF y beneficio. Dime también el
   **modelado** que tenías (Cada tick / Ticks reales / OHLC 1 minuto) y si el EA era "XAUUSD_SupplyDemand_RSI_EA" o "(1)".

| Candidata | Informe | Pasada |
|---|---|---|
| CAND1 | SIN_REGIMEN_H4_SOLAMENTE | 1400 |
| CAND2 | SIN_REGIMEN_H4_Y_SIN_SOLO_BUSCAR_SEEPS_NUEVOS… | 2815 |
| CAND3 | SIN_REGIMEN_H4_Y_SIN_IGNORAR_FVG_PEQUEÑOS… | 1374 |
| CAND4 | SIN_NADA | 1310 |
| CAND5 | SIN_REGIMEN_H4_Y_SIN_SOLO_BUSCAR_SEEPS_NUEVOS… | 2709 |
| CAND6 | SIN_NADA | 1381 |

Si la caché ya no existe y no se puede recuperar, dímelo: lo documentaremos y usaremos mis `.set` (que llevan los
parámetros de señal exactos de los informes, pero el riesgo y `InpFixedRR` sin verificar).

## Paso 1 — Validar en 2023-2024 (solo cuando el paso 0 esté hecho)
- Carga el `ORIGINAL_CANDx.set` y cambia **solo** `InpRiskPercent` a **0.5**. Fechas **2023.01.01 – 2024.12.31**,
  depósito 25.000 USD, 1:100, modelado **"Cada tick basado en ticks reales"**, sin optimización.
- Guarda cada informe: pestaña **Backtest** → clic derecho → **Report → Open XML** (o HTML) → guárdalo y súbemelo.
  Lleva la lista de operaciones, que necesito para separar por años y calcular la significación.
- Apunta la **calidad del historial** que muestra el informe ("History Quality").
- No cambies nada aunque el resultado sea malo: eso también es información.
