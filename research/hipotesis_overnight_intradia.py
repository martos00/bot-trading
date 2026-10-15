"""
Hipotesis F del nuevo ciclo: asimetria overnight vs. intradia (indices).

Fundamento economico: literatura de equity/index futures (ej. Kelly &
Clark 2011, Cliff-Cooper-Gulen 2008) documenta que buena parte de la
deriva alcista de los indices ocurre OVERNIGHT (Close->Open siguiente),
con la sesion intradia (Open->Close) aportando mucho menos o incluso
negativo en promedio -- mecanismo distinto de cualquier candidata ya
probada (ORB, gap fade, turno de mes).

VIABILIDAD -- POR QUE SOLO USTEC/US500, NO XAUUSD (comprobado antes de
programar, reutilizando un hallazgo YA VERIFICADO en este proyecto):
estrategia_gap_fade.py documento que el "cierre" de barra diaria de
XAUUSD en MetaQuotes-Demo es una PAUSA DE MANTENIMIENTO breve (~1h15m,
y 9-13% de los dias sin pausa alguna), NO el cierre de una sesion con
gap de liquidez real -- oro opera casi 23/5. Medir "overnight" ahi
mediria el mismo artefacto ya descartado, no un fenomeno real. Se
excluye XAUUSD de esta hipotesis por esa razon ya establecida, no se
repite el analisis.

FASE 1 (identificar la ventaja antes de construir señal/SL/TP):
 - ret_overnight[t] = Open[t]/Close[t-1] - 1.
 - ret_intradia[t] = Close[t]/Open[t] - 1.
 - Incertidumbre: bootstrap de bloques de 10 dias, 2000 repeticiones.
 - DECISION (fijada ahora): solo se construye estrategia completa si
   AL MENOS UNA de las dos piezas (overnight o intradia) tiene IC que
   excluye cero Y el mismo signo en USTEC y US500 (los unicos 2
   mercados aplicables). Si no, se cierra aqui sin backtest completo.
"""
import numpy as np
import pandas as pd

from hipotesis_rsi2_sma200 import bootstrap_bloques_ic
from datos_ciclo2 import cargar_ustec_2023_2026, cargar_us500_2023_2026


def descomponer(d, etiqueta):
    d = d.copy()
    d['close_prev'] = d['Close'].shift(1)
    d['ret_overnight'] = d['Open'] / d['close_prev'] - 1.0
    d['ret_intradia'] = d['Close'] / d['Open'] - 1.0
    d['ret_total'] = d['Close'] / d['close_prev'] - 1.0

    print(f"\n--- {etiqueta} (n={d['ret_total'].notna().sum()}) ---")
    resultados = {}
    for col, nombre in [('ret_overnight', 'Overnight (Close[t-1]->Open[t])'),
                         ('ret_intradia', 'Intradia (Open[t]->Close[t])'),
                         ('ret_total', 'Total (Close[t-1]->Close[t])')]:
        vals = d[col].dropna().values
        lo, hi = bootstrap_bloques_ic(vals)
        media = vals.mean()
        significativo = not (lo <= 0 <= hi)
        resultados[nombre] = dict(media=media, significativo=significativo)
        marca = "  <-- IC excluye cero" if significativo else ""
        print(f"  {nombre}: media={media*100:+.5f}%/dia  IC95%=[{lo*100:+.5f}%, {hi*100:+.5f}%]{marca}  "
              f"acumulado aprox. en el periodo={media*len(vals)*100:+.1f}%")
    return resultados


def main():
    print("################ Hipotesis F: asimetria overnight vs. intradia (USTEC/US500) ################")
    r_ustec = descomponer(cargar_ustec_2023_2026(), 'USTEC 2023-2026 (exploratorio)')
    r_us500 = descomponer(cargar_us500_2023_2026(), 'US500 2023-2026 (exploratorio)')

    print("\n--- Comprobacion de la regla de decision pre-registrada ---")
    candidatos = []
    for pieza in ['Overnight (Close[t-1]->Open[t])', 'Intradia (Open[t]->Close[t])']:
        sig_ustec, sig_us500 = r_ustec[pieza]['significativo'], r_us500[pieza]['significativo']
        mismo_signo = np.sign(r_ustec[pieza]['media']) == np.sign(r_us500[pieza]['media'])
        print(f"  {pieza}: significativo USTEC={sig_ustec}, US500={sig_us500}, mismo signo={mismo_signo}")
        if sig_ustec and sig_us500 and mismo_signo:
            candidatos.append(pieza)
    if candidatos:
        print(f"\n  CANDIDATOS que pasan el criterio: {candidatos} -- proceder a construir estrategia completa.")
    else:
        print("\n  NINGUNA pieza cumple el criterio pre-registrado en ambos indices -- SE CIERRA esta "
              "hipotesis aqui, sin construir señal/SL/TP/coste.")


if __name__ == '__main__':
    main()
