"""
Pairs Trading / arbitraje estadistico, siguiendo el mecanismo de
Gatev, Goetzmann & Rouwenhorst (2006, RFS) pero con el hedge ratio
estimado por regresion de cointegracion (Engle-Granger) en vez de
"distancia" simple -- tercera estrategia de la fase "Opcion B" (ver
README).

SELECCION DEL PAR (hecha ANTES de programar ninguna regla de trading,
basada en el test de cointegracion, no en el resultado de ninguna
estrategia): de 7 pares candidatos con relacion economica real
(indices EEUU, cruces de USD con vinculo real), se probo cointegracion
Engle-Granger sobre todo el historico disponible. USTEC-US500 fue el
mas fuerte (p=0,0081, el unico par de indices, correlacion de retornos
diarios 0,933) y el de fundamento economico mas directo (misma
economia subyacente, distinta composicion sectorial -- el spread tiene
una razon estructural para revertir). Nota importante encontrada:
EURUSD-GBPUSD tiene correlacion alta (0,806) pero NO esta cointegrado
(p=0,196) -- correlacion no es cointegracion, no se debe confundir.

DIFERENCIA frente al intento ya cerrado de este proyecto
(estrategia_pares_ustec_us500.py, ciclo autonomo anterior): aquella
version NO verifico cointegracion formal antes de operar el par; esta
si, con test de Engle-Granger explicito (ver resultado arriba) antes
de construir ninguna regla.

REGLAS (unica version, pre-registrada, sin optimizar tras ver resultados):
 - Cada dia: beta = pendiente de la regresion OLS log(USTEC) ~ log(US500)
   sobre los ultimos 120 dias (causal, solo pasado).
 - spread = log(USTEC) - beta*log(US500). z = (spread - media_60d) / std_60d
   (tambien causal, misma ventana que el resto del proyecto para
   volatilidad).
 - Entrada: |z| > 2.0 (umbral clasico de la practica de pairs trading,
   no calibrado con estos datos) y sin posicion abierta en el par.
   z>2 (spread caro) => CORTO USTEC / LARGO US500*beta. z<-2 => opuesto.
 - Entrada al Open del dia siguiente (sin lookahead).
 - Salida: z cruza 0 (reversion completa) o |z|>3.5 (stop -- la
   divergencia sigue creciendo) o 40 dias de sesion (cierre forzoso),
   lo que ocurra primero -- recalculando beta/z cada dia con el mismo
   metodo causal.
 - Coste: spread real de cada pata al entrar y al salir.
 - Control: mismo mecanismo pero con el signo de la señal invertido
   aleatoriamente cada señal (mismo tamaño, misma duracion) -- aisla si
   la REVERSION real (vs. apostar con ese tamaño en cualquier
   direccion) aporta valor.
"""
import sys

import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO

VENTANA_BETA = 120
VENTANA_Z = 60
Z_ENTRADA = 2.0
Z_STOP = 3.5
DIAS_MAX = 40
SEED = 20261015
REPETICIONES_CONTROL = 1000


def preparar_par(nombre_a, nombre_b):
    universo = cargar_universo([nombre_a, nombre_b])
    da, db = universo[nombre_a], universo[nombre_b]
    m = pd.merge(da[['dia', 'Open', 'Close', 'Spread']], db[['dia', 'Open', 'Close', 'Spread']],
                 on='dia', suffixes=('_a', '_b')).sort_values('dia').reset_index(drop=True)
    m['log_a'], m['log_b'] = np.log(m['Close_a']), np.log(m['Close_b'])

    betas, spreads = np.full(len(m), np.nan), np.full(len(m), np.nan)
    for i in range(VENTANA_BETA, len(m)):
        x = m['log_b'].iloc[i - VENTANA_BETA:i].to_numpy()
        y = m['log_a'].iloc[i - VENTANA_BETA:i].to_numpy()
        beta = np.polyfit(x, y, 1)[0]
        betas[i] = beta
        spreads[i] = m['log_a'].iloc[i] - beta * m['log_b'].iloc[i]
    m['beta'], m['spread'] = betas, spreads
    m['z'] = (m['spread'] - pd.Series(spreads).rolling(VENTANA_Z).mean()) / pd.Series(spreads).rolling(VENTANA_Z).std()
    return m


def ejecutar(m, point_a, point_b):
    trades = []
    i = VENTANA_BETA + VENTANA_Z
    en_posicion_hasta = -1
    while i < len(m) - 1:
        if i <= en_posicion_hasta or pd.isna(m['z'].iloc[i]):
            i += 1
            continue
        z0 = m['z'].iloc[i]
        if abs(z0) <= Z_ENTRADA:
            i += 1
            continue

        direccion = 'corto_a_largo_b' if z0 > 0 else 'largo_a_corto_b'
        beta_entrada = m['beta'].iloc[i]
        idx_entrada = i + 1
        precio_a_entrada, precio_b_entrada = m['Open_a'].iloc[idx_entrada], m['Open_b'].iloc[idx_entrada]

        idx_fin = min(idx_entrada + DIAS_MAX, len(m) - 1)
        idx_salida, motivo = idx_fin, 'CIERRE_PLAZO'
        for j in range(idx_entrada, idx_fin + 1):
            zj = m['z'].iloc[j]
            if pd.isna(zj):
                continue
            if abs(zj) >= Z_STOP:
                idx_salida, motivo = j, 'STOP_Z'
                break
            if (z0 > 0 and zj <= 0) or (z0 < 0 and zj >= 0):
                idx_salida, motivo = j, 'REVERSION_Z'
                break

        precio_a_salida, precio_b_salida = m['Open_a'].iloc[idx_salida], m['Open_b'].iloc[idx_salida]
        ret_a = np.log(precio_a_salida / precio_a_entrada)
        ret_b = np.log(precio_b_salida / precio_b_entrada)
        # corto_a_largo_b: ganamos si A cae relativo a B -> ret = -ret_a + beta*ret_b
        # largo_a_corto_b: ganamos si A sube relativo a B -> ret = ret_a - beta*ret_b
        if direccion == 'corto_a_largo_b':
            ret_bruto = -ret_a + beta_entrada * ret_b
        else:
            ret_bruto = ret_a - beta_entrada * ret_b

        coste = (m['Spread_a'].iloc[idx_entrada] * point_a / precio_a_entrada +
                 m['Spread_b'].iloc[idx_entrada] * point_b / precio_b_entrada * beta_entrada +
                 m['Spread_a'].iloc[idx_salida] * point_a / precio_a_salida +
                 m['Spread_b'].iloc[idx_salida] * point_b / precio_b_salida * beta_entrada)
        ret_neto = ret_bruto - coste

        trades.append(dict(dia=m['dia'].iloc[idx_entrada], anio=m['dia'].iloc[idx_entrada].year,
                            direccion=direccion, z_entrada=z0, ret_neto=ret_neto, motivo_salida=motivo,
                            dias_en_mercado=idx_salida - idx_entrada))
        en_posicion_hasta = idx_salida
        i = idx_salida + 1
    return pd.DataFrame(trades)


def metricas(ops):
    if len(ops) == 0:
        return dict(n=0)
    r = ops['ret_neto'].to_numpy()
    pf = r[r > 0].sum() / abs(r[r <= 0].sum()) if r[r <= 0].sum() != 0 else np.nan
    curva = np.concatenate([[0], np.cumsum(r)])
    dd = np.maximum.accumulate(curva) - curva
    return dict(n=len(ops), media=r.mean(), suma=r.sum(), pf=pf, pct_acierto=(r > 0).mean() * 100,
                max_dd=dd.max())


def main():
    m = preparar_par('USTEC', 'US500')
    ops = ejecutar(m, UNIVERSO['USTEC']['point'], UNIVERSO['US500']['point'])
    print(f"\n######## Pairs Trading (cointegracion) -- USTEC/US500 ########")
    print(f"Operaciones: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES.")
        return
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
    print(f"  Motivo salida: {ops['motivo_salida'].value_counts().to_dict()}")
    print(f"  Dias en mercado (media): {ops['dias_en_mercado'].mean():.1f}")
    mt = metricas(ops)
    print(f"\n  n={mt['n']}  Media retorno neto/operacion={mt['media']*100:+.3f}%  Suma={mt['suma']*100:+.2f}%  "
          f"PF={mt['pf']:.3f}  %Acierto={mt['pct_acierto']:.1f}%  Max DD (acumulado)={mt['max_dd']*100:.2f}%")
    for anio, g in ops.groupby('anio'):
        mg = metricas(g)
        print(f"    {anio}: n={mg['n']}  Media={mg['media']*100:+.3f}%  Suma={mg['suma']*100:+.2f}%  PF={mg['pf']:.3f}")

    rng = np.random.default_rng(SEED)
    medias_control = []
    for _ in range(REPETICIONES_CONTROL):
        signo_aleatorio = rng.choice([-1, 1], size=len(ops))
        medias_control.append((ops['ret_neto'].to_numpy() * signo_aleatorio).mean())
        # nota: invertir el signo del retorno ya obtenido aproxima "misma magnitud, direccion aleatoria"
    medias_control = np.array(medias_control)
    media_real = ops['ret_neto'].mean()
    z = (media_real - medias_control.mean()) / medias_control.std() if medias_control.std() > 0 else np.nan
    print(f"\n  Control direccion aleatoria: media real={media_real*100:+.4f}%  "
          f"media aleatoria={medias_control.mean()*100:+.4f}%  z={z:+.2f}")


if __name__ == '__main__':
    main()
