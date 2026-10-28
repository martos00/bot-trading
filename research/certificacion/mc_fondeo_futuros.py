"""Ciclo completo en una cuenta de fondeo de futuros típica (50.000 $): examen con objetivo +6 % y pérdida máxima arrastrada 4 % (fin de día,
se bloquea en el saldo inicial); cuota 150 $ por intento; si suspende, paga otro (máx. 10). Fondeada: misma pérdida máxima; cada mes retira
lo que supere +4 % (colchón), reparto 90 %. Se pierde la fondeada → vuelve a empezar con examen. Horizonte 24 meses."""
import numpy as np, pandas as pd
X = pd.read_csv('cartera_fut_diaria.csv', index_col=0, parse_dates=True)
rng = np.random.default_rng(11); B = 20; T = 504; CAP = 50000; CUOTA = 150
def camino(p):
    st = rng.integers(0, len(p) - B, T // B + 1); return p[(st[:, None] + np.arange(B)).ravel()[:T]]
def simula(p):
    R = camino(p); t = 0; pagado = 0; retirado = 0.0; fondeos = 0; perdidas = 0; t_fondeo = None; sobrevive12 = None; primero = None
    while t < T:
        pagado += CUOTA; eq = hwm = 0.0                          # examen
        while t < T:
            eq += R[t]; t += 1; hwm = min(max(hwm, eq), 0.04)
            if eq <= hwm - 0.04: break
            if eq >= 0.06: break
        if primero is None: primero = eq >= 0.06
        if t >= T or eq < 0.06: continue
        fondeos += 1; t_fondeo = t if t_fondeo is None else t_fondeo; ini = t
        eq = hwm = 0.0; vivo = True
        while t < T:
            eq += R[t]; t += 1; hwm = min(max(hwm, eq), 0.04)
            if eq <= hwm - 0.04: vivo = False; break
            if (t - ini) % 21 == 0 and eq > 0.04 + 0.0:
                retirado += 0.9 * (eq - 0.04) * CAP; eq = 0.04
        if sobrevive12 is None: sobrevive12 = vivo or (t - ini) >= 252
        if not vivo: perdidas += 1
        else: break
    return pagado, retirado, fondeos, perdidas, t_fondeo, sobrevive12, primero
for c, nombre in (('E', 'B (firma permisiva)'), ('A', 'A (firma normal, cierre 16:45)')):
    x = X[c].values; m = x.mean() * 252
    print(f'\n=== Cartera {nombre}, Sharpe {x.mean()/x.std()*np.sqrt(252):.2f} ===')
    print('rent. objetivo | riesgo/op | aprueba 1.er examen | exámenes pagados (24 m) | meses hasta fondeada | fondeada dura ≥12 m | pierde la fondeada (24 m) | retirado 24 m (media / mediana) | neto 24 m (media)')
    for obj in (0.06, 0.10, 0.15, 0.25):
        p = x * obj / m; S = [simula(p) for _ in range(4000)]
        pg = np.array([s[0] for s in S]); rt = np.array([s[1] for s in S]); tf = np.array([s[4] if s[4] else np.nan for s in S])
        s12 = np.array([s[5] for s in S if s[5] is not None]); pe = np.array([s[3] > 0 for s in S]); f1 = np.array([bool(s[6]) for s in S]); neg = ((rt - pg) < 0).mean()
        print(f'{obj*100:5.0f} % | {0.5*obj/m:.2f} % | {f1.mean()*100:3.0f} % | {pg.mean()/CUOTA:.1f} | {np.nanmedian(tf)/21:4.1f} | {s12.mean()*100:3.0f} % | {pe.mean()*100:3.0f} % | {rt.mean():,.0f} $ / {np.median(rt):,.0f} $ | {(rt-pg).mean():,.0f} $ | P(acabar perdiendo dinero) {neg*100:.0f} %')
