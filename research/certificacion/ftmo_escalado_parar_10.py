"""FTMO escalado con la regla «subir riesgo y dejar de operar al llegar al +10 % hasta el escalado» (informativo, no es una ventaja).
Reglas FTMO (web 2-nov-2026): +25 % cada 4 meses si +10 % neto en esos 4 meses, 2 cobros y saldo positivo; tope 2 M$.
Supuestos: examen 2 fases (+10 %, +5 %) al mismo riesgo, cuota 1.080 $ por 200K; pérdida máx. 10 % fija y diaria 5 %;
reparto 80 % (90 % tras el primer escalado); en cada ventana de 4 meses (84 días) se opera hasta +10 % y se para; lo ganado se cobra.
Serie: cartera CFD C116 (costes Upcomers) con el beneficio rebajado al 79 % para aproximar los costes de FTMO (Sharpe 1,76 vs 2,24).
Uso: python3 ftmo_escalado_parar_10.py series_planes_10k.csv"""
import sys, numpy as np, pandas as pd
U = pd.read_csv(sys.argv[1], index_col=0)['U'].dropna().values
U = U - U.mean() * (1 - 0.79)
rng = np.random.default_rng(11); B = 20; T = 252 * 10; V = 84; INI = 200_000; CUOTA = 1080
def sim(x, modo):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; anual = np.zeros(10); esc_tot = 0; perdidas = 0; llega = None
    while t < T:
        anual[min(t // 252, 9)] -= CUOTA; ok = True
        for obj in (0.10, 0.05):
            eq = 0.0
            while t < T:
                r = R[t]; t += 1; eq += max(r, -0.05)
                if eq <= -0.10 or r <= -0.05: ok = False; break
                if eq >= obj: break
            if not ok: break
        if not ok or t >= T: continue
        cap = INI; split = 0.8; eq = 0.0; vivo = True
        while t < T and vivo:
            fin = t + V; parado = eq >= 0.10
            while t < min(fin, T):
                r = R[t]; t += 1
                if parado: continue
                eq += max(r, -0.05)
                if eq <= -0.10 or r <= -0.05: vivo = False; perdidas += 1; break
                if eq >= 0.10: parado = True
            if not vivo or t >= T: break
            if eq > 0: anual[min(t // 252, 9)] += split * eq * cap
            if eq >= 0.10 and cap < 2_000_000:
                cap = min(cap + 0.25 * (INI if modo == 'inicial' else cap), 2_000_000); split = 0.9; esc_tot += 1
                if cap >= 2_000_000 and llega is None: llega = t / 252
            eq = min(eq, 0.0)
    return anual, esc_tot, perdidas, llega
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    for modo in ('inicial', 'actual'):
        for r in (0.65, 1.0, 1.5, 2.0):
            x = (U - U.mean() * (1 - hair)) * r / 0.5
            res = [sim(x, modo) for _ in range(1000)]
            A = np.array([a for a, *_ in res]); E = np.array([e for _, e, _, _ in res]); P = np.array([p for _, _, p, _ in res])
            L = np.array([l if l else np.nan for *_, l in res])
            print(f'{et} 25 % del {modo:7s} riesgo {r:4.2f}: escalados en 10 años (mediana) {np.median(E):4.0f} | llega a 2 M$ en 10 años {np.mean(~np.isnan(L)):4.0%}'
                  f' | pierde la cuenta (media en 10 años) {P.mean():4.1f} | neto al mes: año 1 {A[:,0].mean()/12:7,.0f} | año 3 {A[:,2].mean()/12:7,.0f} | año 5 {A[:,4].mean()/12:7,.0f} | año 10 {A[:,9].mean()/12:7,.0f} $')
