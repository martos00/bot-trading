#!/usr/bin/env python3
"""
Analizador del log CSV generado por XAUUSD_SupplyDemand_RSI_EA.mq5
(estrategia Liquidity Sweep -> MSS -> FVG Retest).

El Strategy Tester de MetaTrader 5 no calcula de forma nativa CAGR,
Sortino, ni desgloses LONG/SHORT o por tipo de liquidity zone. Este
script complementario lee el CSV que el EA escribe en cada operación
cerrada (carpeta MQL5/Files/ del terminal, o Tester/Files/ si se
ejecutó en el Strategy Tester) y calcula las métricas del punto 13 del
encargo.

Uso:
    python3 analizar_backtest.py ruta/al/LiquiditySweepMSS_FVG_Log.csv [--balance-inicial 10000]

No inventa datos: si el CSV está vacío o no existe, lo dice explícitamente
en vez de simular un resultado.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import numpy as np


COLUMNAS_ESPERADAS = [
    "FechaHoraApertura", "FechaHoraCierre", "Direccion", "TipoZonaLiquidez",
    "ImportanciaZona", "PrecioSweep", "SweepDistancia", "MSSLevel", "FVGSuperior",
    "FVGInferior", "PrecioEntrada", "StopLoss", "TakeProfit", "RRPlan", "ResultadoR",
    "ResultadoMonetario", "DuracionMinutos", "DrawdownDuranteTrade", "Regimen4H",
]


def cargar_operaciones(ruta_csv: Path) -> pd.DataFrame:
    if not ruta_csv.exists():
        print(f"ERROR: no existe el archivo '{ruta_csv}'. No se ha ejecutado ningún "
              f"backtest todavía, o el EA no ha cerrado ninguna operación con "
              f"InpRegistrarCSV activado.")
        sys.exit(1)

    df = pd.read_csv(ruta_csv, sep=";", header=0, names=COLUMNAS_ESPERADAS, decimal=".")
    if df.empty:
        print(f"AVISO: '{ruta_csv}' existe pero no contiene ninguna operación cerrada. "
              f"No hay métricas que calcular.")
        sys.exit(0)

    df["FechaHoraApertura"] = pd.to_datetime(df["FechaHoraApertura"], format="%Y.%m.%d %H:%M:%S")
    df["FechaHoraCierre"] = pd.to_datetime(df["FechaHoraCierre"], format="%Y.%m.%d %H:%M:%S")
    df = df.sort_values("FechaHoraCierre").reset_index(drop=True)
    return df


def racha_maxima(es_ganadora: pd.Series) -> tuple[int, int]:
    """Devuelve (mayor racha de ganadoras, mayor racha de perdedoras)."""
    max_win = max_loss = cur_win = cur_loss = 0
    for gano in es_ganadora:
        if gano:
            cur_win += 1
            cur_loss = 0
        else:
            cur_loss += 1
            cur_win = 0
        max_win = max(max_win, cur_win)
        max_loss = max(max_loss, cur_loss)
    return max_win, max_loss


def calcular_metricas(df: pd.DataFrame, balance_inicial: float) -> dict:
    n = len(df)
    resultado = df["ResultadoMonetario"]
    resultado_r = df["ResultadoR"]
    ganadoras = resultado > 0
    perdedoras = resultado < 0

    net_profit = resultado.sum()

    # --- Curva de equity reconstruida (balance acumulado tras cada cierre) ---
    equity = balance_inicial + resultado.cumsum()
    equity_con_inicio = pd.concat([pd.Series([balance_inicial]), equity], ignore_index=True)
    pico = equity_con_inicio.cummax()
    drawdown_pct = (equity_con_inicio - pico) / pico * 100.0
    max_drawdown_pct = drawdown_pct.min()
    max_drawdown_abs = (pico - equity_con_inicio).max()

    dias_totales = (df["FechaHoraCierre"].iloc[-1] - df["FechaHoraApertura"].iloc[0]).total_seconds() / 86400.0
    anios = dias_totales / 365.25 if dias_totales > 0 else np.nan
    cagr_pct = (((equity.iloc[-1] / balance_inicial) ** (1.0 / anios)) - 1.0) * 100.0 if anios and anios > 0 else np.nan

    # --- Sharpe / Sortino a partir del R por operación (aproximación a nivel de
    #     trade, no de periodo calendario; ver aviso en el informe) ---
    media_r = resultado_r.mean()
    std_r = resultado_r.std(ddof=1) if n > 1 else np.nan
    sharpe_trade = (media_r / std_r) * np.sqrt(n) if std_r and std_r > 0 else np.nan

    r_negativos = resultado_r[resultado_r < 0]
    std_downside = r_negativos.std(ddof=1) if len(r_negativos) > 1 else np.nan
    sortino_trade = (media_r / std_downside) * np.sqrt(n) if std_downside and std_downside > 0 else np.nan

    ganancia_bruta = resultado[ganadoras].sum()
    perdida_bruta = resultado[perdedoras].sum()  # negativo
    profit_factor = (ganancia_bruta / abs(perdida_bruta)) if perdida_bruta != 0 else np.nan

    win_rate_pct = ganadoras.mean() * 100.0
    avg_win = resultado[ganadoras].mean() if ganadoras.any() else 0.0
    avg_loss = resultado[perdedoras].mean() if perdedoras.any() else 0.0
    expectancy = resultado.mean()

    max_win_streak, max_loss_streak = racha_maxima(ganadoras.tolist())

    exposicion_media_min = df["DuracionMinutos"].mean()

    return dict(
        net_profit=net_profit,
        cagr_pct=cagr_pct,
        max_drawdown_pct=max_drawdown_pct,
        max_drawdown_abs=max_drawdown_abs,
        sharpe_trade=sharpe_trade,
        sortino_trade=sortino_trade,
        profit_factor=profit_factor,
        win_rate_pct=win_rate_pct,
        avg_win=avg_win,
        avg_loss=avg_loss,
        expectancy=expectancy,
        num_operaciones=n,
        r_medio=media_r,
        mejor_operacion=resultado.max(),
        peor_operacion=resultado.min(),
        max_win_streak=max_win_streak,
        max_loss_streak=max_loss_streak,
        exposicion_media_min=exposicion_media_min,
        dias_totales=dias_totales,
    )


def imprimir_metricas(titulo: str, m: dict) -> None:
    print(f"\n=== {titulo} ({m['num_operaciones']} operaciones) ===")
    print(f"  Net Profit:              {m['net_profit']:.2f}")
    print(f"  CAGR:                    {m['cagr_pct']:.2f}%" if not np.isnan(m['cagr_pct']) else "  CAGR:                    N/D (rango temporal insuficiente)")
    print(f"  Max Drawdown:            {m['max_drawdown_pct']:.2f}%  ({m['max_drawdown_abs']:.2f} en moneda de cuenta)")
    print(f"  Sharpe (por operación):  {m['sharpe_trade']:.3f}" if not np.isnan(m['sharpe_trade']) else "  Sharpe (por operación):  N/D")
    print(f"  Sortino (por operación): {m['sortino_trade']:.3f}" if not np.isnan(m['sortino_trade']) else "  Sortino (por operación): N/D")
    print(f"  Profit Factor:           {m['profit_factor']:.3f}" if not np.isnan(m['profit_factor']) else "  Profit Factor:           N/D")
    print(f"  Win Rate:                {m['win_rate_pct']:.2f}%")
    print(f"  Average Win:             {m['avg_win']:.2f}")
    print(f"  Average Loss:            {m['avg_loss']:.2f}")
    print(f"  Expectancy (por op.):    {m['expectancy']:.2f}")
    print(f"  R medio por operación:   {m['r_medio']:.3f}")
    print(f"  Mejor operación:         {m['mejor_operacion']:.2f}")
    print(f"  Peor operación:          {m['peor_operacion']:.2f}")
    print(f"  Rachas: {m['max_win_streak']} ganadoras / {m['max_loss_streak']} perdedoras (máximas consecutivas)")
    print(f"  Exposición media:        {m['exposicion_media_min']:.1f} min/operación")
    print(f"  Rango temporal cubierto: {m['dias_totales']:.1f} días")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Ruta al CSV exportado por el EA")
    parser.add_argument("--balance-inicial", type=float, default=10000.0,
                         help="Balance inicial de la cuenta usada en el backtest (para CAGR/Drawdown). Por defecto 10000.")
    args = parser.parse_args()

    df = cargar_operaciones(args.csv)

    print(f"Cargadas {len(df)} operaciones desde {args.csv}")
    print(f"Periodo: {df['FechaHoraApertura'].min()} -> {df['FechaHoraCierre'].max()}")

    global_metricas = calcular_metricas(df, args.balance_inicial)
    imprimir_metricas("TODAS LAS OPERACIONES", global_metricas)

    for direccion in ("LONG", "SHORT"):
        subset = df[df["Direccion"] == direccion]
        if not subset.empty:
            imprimir_metricas(f"SÓLO {direccion}", calcular_metricas(subset, args.balance_inicial))
        else:
            print(f"\n=== SÓLO {direccion} ===\n  Sin operaciones en esta dirección.")

    print("\n--- Desglose por tipo de liquidity zone ---")
    for zona, subset in df.groupby("TipoZonaLiquidez"):
        m = calcular_metricas(subset, args.balance_inicial)
        print(f"\n  Zona: {zona}  ({m['num_operaciones']} operaciones)")
        print(f"    Net Profit: {m['net_profit']:.2f}   Win Rate: {m['win_rate_pct']:.2f}%   "
              f"Profit Factor: {m['profit_factor']:.3f}   R medio: {m['r_medio']:.3f}")

    print("\nAVISO: Sharpe/Sortino aquí son aproximaciones a nivel de operación "
          "(no de periodo calendario), útiles para comparar configuraciones entre sí, "
          "no como cifra absoluta comparable a un fondo que reporta Sharpe diario/mensual. "
          "El Max Drawdown se reconstruye sólo a partir de los resultados de este log "
          "(no incluye flotante intra-operación de otras posiciones simultáneas, ya que "
          "el EA gestiona una única posición a la vez).")


if __name__ == "__main__":
    main()
