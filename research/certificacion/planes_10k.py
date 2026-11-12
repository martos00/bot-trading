"""Comparación de TODOS los planes para llegar a 10.000 $/mes (12-nov-2026). Simulación conjunta: en cada trayectoria todas las cuentas
viven los mismos días de mercado (bloques de 20 días de 2018-2026, mismas fechas en las 4 series de series_planes_10k.csv).
Métrica: «capacidad de ingreso» del mes = lo cobrado neto de las prop firms en los últimos 12 meses (cobros − exámenes) + rentabilidad
anual esperada de la cuenta propia (capital × rentabilidad esperada del escenario). Llega a 10k/mes cuando eso ≥ 120.000 $.
Se informa también el dinero propio que hay que adelantar (peor saldo de caja) y lo cobrado en los años 1-3.

Modelos (reglas: ver docstrings de upcomers_horizon_reglas_confirmadas.py, tradeify_50k_actual.py; supuestos marcados con *):
- Upcomers Horizon (serie U): examen 9 %, diaria 3 %, 6 % arrastrada que se fija en el inicial; cobro con 3 % entre cobros, 3 días ≥ 0,5 %,
  cada 10 hábiles, 80 %, 19,9 $ + 2,49 %, topes 5k..30k en cuentas ≥ 800K, colchón 3 %. 50K 103 $, 1,5M 2.300 $, 2M 2.900 $*.
  UNA sola cuenta grande por persona* (reseñas: tope total por persona).
- Tradeify Flex (serie T): 50K 165 $ (reset 109), objetivo 3.000, 2.000 EOD que se fija en +100*, consistencia 40 % en el examen;
  cobro tras 5 días ≥ 150 $, mín(50 % del beneficio, 2.500), 90 %. 150K 369 $ (reset 239), objetivo 9.000, 4.500 EOD, días ≥ 250 $,
  tope 4.500 $*. Máx. 5 cuentas*. (Paso obligatorio a cuenta real tras 3 cobros: NO modelado.)
- Lucid Flex 50K (serie T; bots SIN confirmar): 115 $* (reset 80), mismas reglas que Tradeify 50K, tope por cobro 2.000 $*. Máx. 5*.
- Tipo FTMO 200K (serie F, costes de FTMO; también aproxima FXIFY/Alpha/E8 con costes parecidos): 1.250 $ (devuelto con el 1.er cobro),
  10 % + 5 %, diaria 5 %, máx. 10 % fija; cobro cada 10 hábiles de todo el beneficio, 80 % (90 % tras escalar); escalado +25 % cada
  84 hábiles si el ciclo gana ≥ 10 % con ≥ 2 cobros, hasta 2M. Máx. 2 cuentas (400K)*.
- Cuenta propia (serie O, futuros cartera completa) a riesgo 0,8: solo en los planes H, I, J (60.000 $ iniciales + el % indicado de los cobros).
Riesgos: Upcomers examen 1,5 (50K) / 1,0 (grande), fondeada 0,8; Tradeify/Lucid examen 1,0, fondeada 0,8; FTMO examen 1,25, fondeada 1,0.
Uso: python3 planes_10k.py SERIES_CSV"""
import sys, numpy as np, pandas as pd
D = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)
TOP = [5000, 7500, 10000, 15000, 20000, 25000, 30000]; B = 20; T = 1260; NS = 800

class Upc:
    def __init__(s, cap, precio, re, rf): s.cap, s.precio, s.re, s.rf, s.ser = cap, precio, re, rf, 'U'; s.nueva()
    def nueva(s): s.f = 0; s.eq = s.h = 0.0; s.k = 0
    def dia(s, r5, t):
        if s.f == 0:
            r = r5 * s.re / 0.5; s.eq += r; s.h = max(s.h, s.eq)
            if r <= -0.03 or s.eq <= min(s.h, 0.06) - 0.06: s.nueva(); return 0.0, s.precio
            if s.eq >= 0.09: s.f = 1; s.b = s.h = s.b0 = 0.0; s.d = 0; s.i = t
            return 0.0, 0.0
        r = r5 * s.rf / 0.5; s.b += r; s.h = max(s.h, s.b)
        if r >= 0.005: s.d += 1
        if r <= -0.03 or s.b <= min(s.h - 0.06, 0.0): s.nueva(); return 0.0, s.precio
        if (t - s.i) % 10 == 0 and s.b - s.b0 >= 0.03 and s.d >= 3 and s.b > 0.03:
            q = (s.b - 0.03) * s.cap
            if s.cap >= 800_000 and s.k < len(TOP): q = min(q, TOP[s.k])
            s.b -= q / s.cap; s.b0 = s.b; s.k += 1; s.d = 0; return 0.8 * q * (1 - 0.0249) - 19.9, 0.0
        return 0.0, 0.0

class Fut:   # Tradeify / Lucid Flex
    def __init__(s, cap, reset, obj, dd, minday, tope, re, rf, split=0.9):
        s.cap, s.reset, s.obj, s.dd, s.minday, s.tope, s.re, s.rf, s.split, s.ser = cap, reset, obj, dd, minday, tope, re, rf, split, 'T'; s.nueva()
    def nueva(s): s.f = 0; s.b = s.h = s.mx = 0.0
    def dia(s, r5, t):
        if s.f == 0:
            r = r5 * s.re / 0.5 * s.cap; s.b += r; s.h = min(max(s.h, s.b), s.dd + 100); s.mx = max(s.mx, r)
            if s.b <= s.h - s.dd: s.nueva(); return 0.0, s.reset
            if s.b >= s.obj and s.mx <= 0.4 * s.b: s.f = 1; s.b = s.h = 0.0; s.d = 0
            return 0.0, 0.0
        r = r5 * s.rf / 0.5 * s.cap; s.b += r; s.h = min(max(s.h, s.b), s.dd + 100)
        if s.b <= s.h - s.dd: s.nueva(); return 0.0, s.reset
        if r >= s.minday: s.d += 1
        if s.d >= 5 and s.b > 0:
            q = min(0.5 * s.b, s.tope); s.b -= q; s.d = 0; return s.split * q, 0.0
        return 0.0, 0.0

class Ftmo:
    def __init__(s, re=1.25, rf=1.0, precio=1250): s.re, s.rf, s.precio, s.ser = re, rf, precio, 'F'; s.cap0 = 200_000; s.nueva(True)
    def nueva(s, primera=False): s.f = 0; s.fase = 0; s.eq = 0.0; s.cap = s.cap0; s.devuelto = False
    def dia(s, r5, t):
        if s.f == 0:
            r = r5 * s.re / 0.5; s.eq += r
            if r <= -0.05 or s.eq <= -0.10: s.nueva(); return 0.0, s.precio
            if s.eq >= (0.10, 0.05)[s.fase]:
                s.fase += 1; s.eq = 0.0
                if s.fase == 2: s.f = 1; s.b = 0.0; s.i = t; s.c0 = t; s.cic = 0.0; s.nc = 0; s.sp = 0.8
            return 0.0, 0.0
        r = r5 * s.rf / 0.5; s.b += r
        if r <= -0.05 or s.b <= -0.10: s.nueva(); return 0.0, s.precio
        c = 0.0
        if (t - s.i) % 10 == 0 and s.b > 0:
            q = s.b * s.cap; s.cic += s.b; s.b = 0.0; s.nc += 1; c = s.sp * q
            if not s.devuelto: c += s.precio; s.devuelto = True
        if t - s.c0 >= 84:
            if s.cic + max(s.b, 0) >= 0.10 and s.nc >= 2 and s.cap < 2_000_000: s.cap = min(s.cap * 1.25, 2_000_000); s.sp = 0.9
            s.c0 = t; s.cic = 0.0; s.nc = 0
        return c, 0.0

def u50(): return Upc(50_000, 103, 1.5, 0.8)
def ugr(): return Upc(2_000_000, 2900, 1.0, 0.8)
def t50(): return Fut(50_000, 109, 3000, 2000, 150, 2500, 1.0, 0.8)
def t150(): return Fut(150_000, 239, 9000, 4500, 250, 4500, 1.0, 0.8)
def l50(): return Fut(50_000, 80, 3000, 2000, 150, 2000, 1.0, 0.8)
PRECIO = {'u50': 103, 'ugr': 2900, 't50': 165, 't150': 369, 'l50': 115, 'ftmo': 1250}
FAB = {'u50': u50, 'ugr': ugr, 't50': t50, 't150': t150, 'l50': l50, 'ftmo': Ftmo}

PLANES = {   # inicio: cuentas compradas el día 0; compra: lista de (tipo, máximo) que se compran con la caja en orden; propia: % de cobros a la cuenta propia
    'A  Upcomers 2M ya':                         dict(inicio=['ugr'], compra=[], propia=0.0, p0=0),
    'B  Upcomers 50K → 2M':                      dict(inicio=['u50'], compra=[('ugr', 1)], propia=0.0, p0=0),
    'C  Tradeify 50K → hasta 5 de 150K':         dict(inicio=['t50'], compra=[('t150', 5)], propia=0.0, p0=0),
    'D  Tradeify + Lucid (hasta 5 + 5)':         dict(inicio=['t50', 'l50'], compra=[('t150', 5), ('l50', 5)], propia=0.0, p0=0),
    'E  2× tipo FTMO 200K ya':                   dict(inicio=['ftmo', 'ftmo'], compra=[], propia=0.0, p0=0),
    'F  Upcomers 2M + 2× FTMO ya':               dict(inicio=['ugr', 'ftmo', 'ftmo'], compra=[], propia=0.0, p0=0),
    'G  Todo ya (2M + 2 FTMO + T50 + L50) y reinvertir en futuros': dict(inicio=['ugr', 'ftmo', 'ftmo', 't50', 'l50'], compra=[('t150', 5), ('l50', 5)], propia=0.0, p0=0),
    'H  Solo cuenta propia 60K (riesgo 0,8)':     dict(inicio=[], compra=[], propia=0.0, p0=60_000),
    'I  G + cuenta propia 60K + 50 % de los cobros a ella': dict(inicio=['ugr', 'ftmo', 'ftmo', 't50', 'l50'], compra=[('t150', 5), ('l50', 5)], propia=0.5, p0=60_000),
    'J  Upcomers 50K → 2M + cuenta propia 60K + 50 % a ella': dict(inicio=['u50'], compra=[('ugr', 1)], propia=0.5, p0=60_000),
}

def corre(hair, et):
    X = {k: (D[k] - D[k].mean() * (1 - hair)).values for k in D}
    erO = (D['O'].mean() * hair) * 252 * 0.8 / 0.5                  # rentabilidad anual esperada de la cuenta propia en el escenario
    for nom, plan in PLANES.items():
        rng = np.random.default_rng(42); L = []; Y1 = []; Y2 = []; Y3 = []; MC = []; PF = []
        for _ in range(NS):
            st = rng.integers(0, len(X['U']) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; R = {k: X[k][idx] for k in X}
            cs = []; tipos = []; caja = 0.0; minc = 0.0; propia = float(plan['p0']); neto = np.zeros(T); pm = []
            for k in plan['inicio']: cs.append(FAB[k]()); tipos.append(k); caja -= PRECIO[k]; neto[0] -= PRECIO[k]
            minc = caja
            for t in range(T):
                propia *= 1 + R['O'][t] * 0.8 / 0.5
                for c in cs:
                    q, g = c.dia(R[c.ser][t], t)
                    if q > 0: a = q * plan['propia']; propia += a; q -= a
                    caja += q - g; neto[t] += q - g
                for k, mx in plan['compra']:
                    if tipos.count(k) < mx and caja >= PRECIO[k] + 200 and not (k == 'ugr' and 'ugr' in tipos):
                        cs.append(FAB[k]()); tipos.append(k); caja -= PRECIO[k]; neto[t] -= PRECIO[k]
                minc = min(minc, caja)
                if t % 21 == 20: pm.append(propia)
            m = np.add.reduceat(neto, np.arange(0, T, 21))[:len(pm)]
            doce = np.convolve(m, np.ones(12), 'full')[:len(m)]
            capac = doce + np.array(pm) * erO
            L.append(np.argmax(capac >= 120_000) + 1 if (capac >= 120_000).any() else np.nan)
            Y1.append(m[:12].sum()); Y2.append(m[12:24].sum()); Y3.append(m[24:36].sum()); MC.append(minc); PF.append(pm[-1])
        L = np.array(L, float)
        print(f'{et:8s} | {nom:62s} | 10k/mes: 2 años {np.mean(L<=24)*100:3.0f} %, 3 años {np.mean(L<=36)*100:3.0f} %, 5 años {np.mean(L<=60)*100:3.0f} %, mes mediano {np.nanmedian(L) if np.isfinite(L).any() else float("nan"):4.0f} '
              f'| prop neto (mediana) año1 {np.median(Y1):8,.0f} año2 {np.median(Y2):8,.0f} año3 {np.median(Y3):8,.0f} | adelantar {-np.median(MC):6,.0f} $ (peor 10 % {-np.percentile(MC,10):6,.0f}) | cuenta propia a 5 años {np.median(PF):10,.0f} $', flush=True)

for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')): corre(hair, et)
