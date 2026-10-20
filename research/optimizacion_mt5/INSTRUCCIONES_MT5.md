# Qué tienes que hacer en MetaTrader 5 (unos 30-60 minutos)

Archivos: `research/optimizacion_mt5/CAND1...CAND4*.set`. Cópialos a `MQL5\Profiles\Tester\` de tu terminal
(Archivo → Abrir carpeta de datos), o cárgalos desde el Probador: pestaña **Parámetros** → clic derecho → **Cargar**.

## Paso 0 — Reproducir (1 prueba por candidata)
- Experto `XAUUSD_SupplyDemand_RSI_EA`, símbolo XAUUSD, M15, fechas **2025.01.02 – 2026.09.21**, depósito 25.000 USD,
  apalancamiento 1:100, modelado **"Cada tick basado en ticks reales"**, optimización **desactivada**.
- Carga el `.set`. **Cambia `InpRiskPercent` al valor que usaste en aquella optimización** (si no lo recuerdas, déjalo en 0,5).
- Dime para cada candidata: operaciones, profit factor y beneficio neto.

## Paso 1 — Validar en 2023-2024 (lo importante)
- Mismo `.set` con **`InpRiskPercent = 0.5`**, fechas **2023.01.01 – 2024.12.31**.
- Para cada candidata, guarda el informe: pestaña **Backtest** (informe) → clic derecho → **Report → Open XML** (o HTML) y
  guárdalo; súbelo aquí. Así tengo cada operación para el Monte Carlo de fondeo.
- Anota la **calidad del historial** que aparece en el informe (por ejemplo "History Quality 100% real ticks").

No hace falta abrir cuentas ni dinero real: el Probador funciona con la cuenta demo de MetaQuotes.
Si el servidor no tiene ticks reales de 2023-2024, dímelo y lo hacemos con "OHLC de 1 minuto", declarándolo.
