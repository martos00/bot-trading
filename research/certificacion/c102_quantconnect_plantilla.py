from AlgorithmImports import *
import numpy as np, pandas as pd
MERCADO = '__MERCADO__'
DESFASE_H = __DESFASE__
MODO = '__MODO__'
FEST = set('20110117,20110221,20110422,20110530,20110704,20110905,20111124,20111226,20120102,20120116,20120220,20120406,20120528,20120704,20120903,20121029,20121030,20121122,20121225,20130101,20130121,20130218,20130329,20130527,20130704,20130902,20131128,20131225,20140101,20140120,20140217,20140418,20140526,20140704,20140901,20141127,20141225,20150101,20150119,20150216,20150403,20150525,20150703,20150907,20151126,20151225,20160101,20160118,20160215,20160325,20160530,20160704,20160905,20161124,20161226,20170102,20170116,20170220,20170414,20170529,20170704,20170904,20171123,20171225,20180101,20180115,20180219,20180330,20180528,20180704,20180903,20181122,20181205,20181225,20190101,20190121,20190218,20190419,20190527,20190704,20190902,20191128,20191225,20200101,20200120,20200217,20200410,20200525,20200703,20200907,20201126,20201225,20210101,20210118,20210215,20210402,20210531,20210705,20210906,20211125,20211224,20220117,20220221,20220415,20220530,20220620,20220704,20220905,20221124,20221226,20230102,20230116,20230220,20230407,20230529,20230619,20230704,20230904,20231123,20231225,20240101,20240115,20240219,20240329,20240527,20240619,20240704,20240902,20241128,20241225,20250101,20250109,20250120,20250217,20250418,20250526,20250619,20250704,20250901,20251127,20251225,20260101,20260119,20260216,20260403,20260525,20260619,20260703,20260907,20261126,20261225'.split(','))
def t_nw(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n < 10: return float('nan')
    e = x - x.mean(); g = [e[k:] @ e[:n - k] / n for k in range(L + 1)]
    v = (g[0] + 2 * sum((1 - k / (L + 1)) * g[k] for k in range(1, L + 1))) / n
    return float(x.mean() / np.sqrt(v)) if v > 0 else float('nan')
def simula(x):
    n = x.index; mm = n.hour * 60 + n.minute
    ses = (n + pd.Timedelta(hours=5)).normalize()
    o, h, l, c = (x[k].values for k in ('open', 'high', 'low', 'close')); out = []
    sv = ses.values; dias = pd.DatetimeIndex(np.unique(sv))
    ini, fin = np.searchsorted(sv, dias.values), np.searchsorted(sv, dias.values, 'right')
    for d, a, b in zip(dias, ini, fin):
        if d.weekday() > 4: continue
        m = mm[a:b]; idx = np.arange(a, b)
        rg = idx[(m >= 19 * 60) | (m < 180)]; en = idx[(m >= 180) & (m < 660)]; hasta = idx[(m >= 180) & (m < 1005)]
        if len(rg) < 3 or len(en) == 0 or len(hasta) == 0: continue
        H, L = h[rg].max(), l[rg].min(); W = H - L
        if W <= 0: continue
        up = np.nonzero(h[en] > H)[0]; dn = np.nonzero(l[en] < L)[0]
        iu = up[0] if len(up) else 10**9; idn = dn[0] if len(dn) else 10**9
        if iu == idn: continue
        sg = 1 if iu < idn else -1; i0 = en[min(iu, idn)]
        p0 = max(H, o[i0]) if sg == 1 else min(L, o[i0]); st = L if sg == 1 else H; tg = p0 + sg * W
        res = None
        for i in hasta[hasta >= i0]:
            hs = l[i] <= st if sg == 1 else h[i] >= st
            ht = (h[i] >= tg if sg == 1 else l[i] <= tg) and i != i0
            if hs: res = st; break
            if ht: res = tg; break
        if res is None: res = c[hasta[-1]]
        out.append((d, sg * np.log(res / p0) * 1e4))
    return pd.Series(dict(out)).sort_index()
class C102(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2026, 10, 1); self.set_end_date(2026, 10, 2); self.set_cash(100000)
        f = self.add_future(MERCADO, Resolution.MINUTE, extended_market_hours=True,
                            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
                            data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
        if MODO == 'cal':
            for d in (datetime(2016, 1, 27), datetime(2022, 7, 27)):
                h = self.history(f.symbol, d, d + timedelta(days=1), Resolution.HOUR, extended_market_hours=True)
                s = h['close'].droplevel(list(range(h.index.nlevels - 1))) if h.index.nlevels > 1 else h['close']
                self.log('CAL ' + ' '.join(f'{t:%m%d%H}:{v:.2f}' for t, v in s.items()))
            return
        R = []
        for y in range(2010, 2027):
            for m0 in (1, 4, 7, 10):
                a = datetime(y, m0, 1) - timedelta(days=1); b = datetime(y + (m0 == 10), (m0 + 3 - 1) % 12 + 1, 1)
                if a > datetime(2026, 9, 30) or b < datetime(2010, 6, 1): continue
                h = self.history(f.symbol, a, b, Resolution.MINUTE, extended_market_hours=True)
                if h is None or len(h) == 0: continue
                x = h[['open', 'high', 'low', 'close']]
                x = x.droplevel(list(range(h.index.nlevels - 1))) if h.index.nlevels > 1 else x
                x = x[~x.index.duplicated()].sort_index(); x.index = x.index + pd.Timedelta(hours=DESFASE_H) - pd.Timedelta(minutes=1)
                r = simula(x); r = r[(r.index >= datetime(y, m0, 1)) & (r.index < b)]; R.append(r)
        r = pd.concat(R); r = r[~r.index.duplicated()]; r = r[(r.index >= '2010-06-01') & (r.index <= '2026-09-30')]
        an = r.groupby(r.index.year).mean()
        self.log(f'R {MERCADO} n {len(r)} {r.mean():+.2f} t {t_nw(r.values):.2f} | 2010-19 {r[r.index < "2020"].mean():+.2f} | 2020-26 {r[r.index >= "2020"].mean():+.2f} | anos+ {(an>0).sum()}/{len(an)}')
        self.log('A ' + MERCADO + ' ' + ' '.join(f'{k}:{v:+.1f}' for k, v in an.items()))
