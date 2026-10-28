from AlgorithmImports import *
import numpy as np, pandas as pd
MERCADO = '__MERCADO__'
CHECK = __CHECK__
DESFASE_H = __DESFASE__
FEST = set('20110117,20110221,20110422,20110530,20110704,20110905,20111124,20111226,20120102,20120116,20120220,20120406,20120528,20120704,20120903,20121029,20121030,20121122,20121225,20130101,20130121,20130218,20130329,20130527,20130704,20130902,20131128,20131225,20140101,20140120,20140217,20140418,20140526,20140704,20140901,20141127,20141225,20150101,20150119,20150216,20150403,20150525,20150703,20150907,20151126,20151225,20160101,20160118,20160215,20160325,20160530,20160704,20160905,20161124,20161226,20170102,20170116,20170220,20170414,20170529,20170704,20170904,20171123,20171225,20180101,20180115,20180219,20180330,20180528,20180704,20180903,20181122,20181205,20181225,20190101,20190121,20190218,20190419,20190527,20190704,20190902,20191128,20191225,20200101,20200120,20200217,20200410,20200525,20200703,20200907,20201126,20201225,20210101,20210118,20210215,20210402,20210531,20210705,20210906,20211125,20211224,20220117,20220221,20220415,20220530,20220620,20220704,20220905,20221124,20221226,20230102,20230116,20230220,20230407,20230529,20230619,20230704,20230904,20231123,20231225,20240101,20240115,20240219,20240329,20240527,20240619,20240704,20240902,20241128,20241225,20250101,20250109,20250120,20250217,20250418,20250526,20250619,20250704,20250901,20251127,20251225,20260101,20260119,20260216,20260403,20260525,20260619,20260703,20260907,20261126,20261225'.split(','))
def t_nw(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n < 10: return float('nan')
    e = x - x.mean(); g = [e[k:] @ e[:n - k] / n for k in range(L + 1)]
    v = (g[0] + 2 * sum((1 - k / (L + 1)) * g[k] for k in range(1, L + 1))) / n
    return float(x.mean() / np.sqrt(v)) if v > 0 else float('nan')
class B22(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2026, 10, 1); self.set_end_date(2026, 10, 2); self.set_cash(100000)
        f = self.add_future(MERCADO, Resolution.MINUTE, extended_market_hours=True,
                            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
                            data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
        filas = []
        for y in range(2012, 2027):
            for m0 in (1, 4, 7, 10):
                a = datetime(y, m0, 1); b = datetime(y + (m0 == 10), (m0 + 3 - 1) % 12 + 1, 1)
                if a > datetime(2026, 9, 30): continue
                h = self.history(f.symbol, a - timedelta(hours=7), b, Resolution.MINUTE, extended_market_hours=True)
                if h is None or len(h) == 0: continue
                s = h['close'].droplevel(list(range(h.index.nlevels - 1))) if h.index.nlevels > 1 else h['close']
                s = s[~s.index.duplicated()].sort_index()
                s.index = s.index + pd.Timedelta(hours=DESFASE_H)
                ts = pd.Series(s.index, index=s.index)
                p = s.resample('30min', label='right', closed='right').last()
                tl = ts.resample('30min', label='right', closed='right').last()
                p[(p.index - tl) > pd.Timedelta(minutes=10)] = np.nan
                r = np.log(p.shift(-1) / p)          # franja que empieza en el indice
                r = r[(r.index >= a) & (r.index < b)].dropna()
                filas.append(r)
        R = pd.concat(filas); R = R[~R.index.duplicated()]
        hm = R.index.hour * 100 + R.index.minute
        ok = (hm >= 1800) | (hm <= 1600)
        ok &= ~((hm >= 1630) & (hm < 1800))
        R = R[ok]; hm = R.index.hour * 100 + R.index.minute
        dia = (R.index + pd.Timedelta(hours=6)).normalize()
        df = pd.DataFrame({'r': R.values * 1e4, 'hm': hm, 'dia': dia})
        df = df[df.dia.dt.dayofweek < 5]
        dias = pd.DatetimeIndex(sorted(df.dia.unique()))
        self.log(f'{MERCADO} datos {dias[0].date()} -> {dias[-1].date()} dias {len(dias)}')
        tipo = {}
        sd = pd.Series(dias, index=dias)
        for _, g in sd.groupby([dias.year, dias.month]):
            g = list(g)
            for k, nm in ((-3, 'D-2'), (-2, 'D-1'), (-1, 'D0'), (0, 'D+1'), (1, 'D+2')):
                if len(g) > 5: tipo.setdefault(g[k], []).append(nm)
        fest = FEST
        for d in dias:
            nombres = ['lun', 'mar', 'mie', 'jue', 'vie'][d.dayofweek]
            tipo.setdefault(d, []).append(nombres)
            sig = d + pd.Timedelta(days=1)
            while sig.dayofweek >= 5: sig += pd.Timedelta(days=1)
            ant = d - pd.Timedelta(days=1)
            while ant.dayofweek >= 5: ant -= pd.Timedelta(days=1)
            if sig.strftime('%Y%m%d') in fest and d.strftime('%Y%m%d') not in fest: tipo[d].append('PRE')
            if ant.strftime('%Y%m%d') in fest and d.strftime('%Y%m%d') not in fest: tipo[d].append('POST')
        filas = [(d, t) for d, ts_ in tipo.items() for t in ts_]
        T = pd.DataFrame(filas, columns=['dia', 'tipo'])
        X = df.merge(T, on='dia')
        nreg = 0; sel = []
        for (t, h_), g in X.groupby(['tipo', 'hm']):
            nreg += 1
            g = g.sort_values('dia'); a_ = g[g.dia < '2018-01-01'].r.values; b_ = g[g.dia >= '2018-01-01']
            ta = t_nw(a_); nmin = 250 if t in ('lun', 'mar', 'mie', 'jue', 'vie') else 50
            if len(a_) >= nmin and abs(ta) >= 4.0:
                s_ = np.sign(a_.mean()); tb = t_nw(b_.r.values) * s_
                an = b_.groupby(b_.dia.dt.year).r.mean(); yrs = float((np.sign(an) == s_).mean()) if len(an) else float('nan')
                sel.append(f'SEL {MERCADO} {t} {h_:04d} nd {len(a_)} md {a_.mean():+.2f} td {ta:+.2f} nc {len(b_)} mc {b_.r.mean():+.2f} tc {tb:+.2f} anos {yrs:.2f}')
        top = []
        for (t, h_), g in X.groupby(['tipo', 'hm']):
            a_ = g[g.dia < '2018-01-01'].r.values
            if len(a_) >= 50: top.append((abs(t_nw(a_)), t, h_, a_.mean()))
        top.sort(reverse=True)
        self.log('TOP ' + ' | '.join(f'{t} {h_:04d} {m:+.2f} t{tt:.1f}' for tt, t, h_, m in top[:6]))
        for t, h_ in CHECK:
            g = X[(X.tipo == t) & (X.hm == h_)]; a_ = g[g.dia < '2018-01-01'].r.values; b_ = g[g.dia >= '2018-01-01'].r.values
            self.log(f'CHECK {MERCADO} {t} {h_:04d} desc {a_.mean():+.2f} t {t_nw(a_):+.2f} n {len(a_)} | conf {b_.mean():+.2f} t {t_nw(b_):+.2f} n {len(b_)}')
        self.log(f'{MERCADO} reglas {nreg} seleccionadas {len(sel)}')
        for l in sel[:60]: self.log(l)
    def on_data(self, data):
        pass
