from AlgorithmImports import *
import numpy as np, pandas as pd
MERCADO = '__MERCADO__'
DESFASE_H = 0
FEST = set('20110117,20110221,20110422,20110530,20110704,20110905,20111124,20111226,20120102,20120116,20120220,20120406,20120528,20120704,20120903,20121029,20121030,20121122,20121225,20130101,20130121,20130218,20130329,20130527,20130704,20130902,20131128,20131225,20140101,20140120,20140217,20140418,20140526,20140704,20140901,20141127,20141225,20150101,20150119,20150216,20150403,20150525,20150703,20150907,20151126,20151225,20160101,20160118,20160215,20160325,20160530,20160704,20160905,20161124,20161226,20170102,20170116,20170220,20170414,20170529,20170704,20170904,20171123,20171225,20180101,20180115,20180219,20180330,20180528,20180704,20180903,20181122,20181205,20181225,20190101,20190121,20190218,20190419,20190527,20190704,20190902,20191128,20191225,20200101,20200120,20200217,20200410,20200525,20200703,20200907,20201126,20201225,20210101,20210118,20210215,20210402,20210531,20210705,20210906,20211125,20211224,20220117,20220221,20220415,20220530,20220620,20220704,20220905,20221124,20221226,20230102,20230116,20230220,20230407,20230529,20230619,20230704,20230904,20231123,20231225,20240101,20240115,20240219,20240329,20240527,20240619,20240704,20240902,20241128,20241225,20250101,20250109,20250120,20250217,20250418,20250526,20250619,20250704,20250901,20251127,20251225,20260101,20260119,20260216,20260403,20260525,20260619,20260703,20260907,20261126,20261225'.split(','))
def t_nw(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n < 10: return float('nan')
    e = x - x.mean(); g = [e[k:] @ e[:n - k] / n for k in range(L + 1)]
    v = (g[0] + 2 * sum((1 - k / (L + 1)) * g[k] for k in range(1, L + 1))) / n
    return float(x.mean() / np.sqrt(v)) if v > 0 else float('nan')
class C95(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2026, 10, 1); self.set_end_date(2026, 10, 2); self.set_cash(100000)
        f = self.add_future(MERCADO, Resolution.MINUTE, extended_market_hours=True,
                            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
                            data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
        P = {}
        for y in range(2010, 2027):
            for m0 in (1, 4, 7, 10):
                a = datetime(y, m0, 1); b = datetime(y + (m0 == 10), (m0 + 3 - 1) % 12 + 1, 1)
                if a > datetime(2026, 9, 30) or b < datetime(2010, 6, 1): continue
                h = self.history(f.symbol, a, b, Resolution.MINUTE, extended_market_hours=True)
                if h is None or len(h) == 0: continue
                s = h['close'].droplevel(list(range(h.index.nlevels - 1))) if h.index.nlevels > 1 else h['close']
                s = s[~s.index.duplicated()].sort_index(); s.index = s.index + pd.Timedelta(hours=DESFASE_H)
                d = s.index.normalize(); mm = s.index.hour * 60 + s.index.minute
                for nom, m in (('1330', 810), ('1400', 840), ('1430', 870)):
                    q = s[(mm <= m) & (mm > m - 10)]
                    q = q.groupby(q.index.normalize()).last()
                    P.setdefault(nom, []).append(q)
        X = pd.DataFrame({k: pd.concat(v) for k, v in P.items()})
        X = X[~X.index.duplicated()].sort_index(); X = X[X.index.dayofweek < 5].dropna()
        X = X[[dd.strftime('%Y%m%d') not in FEST for dd in X.index]]
        prev = X['1430'].shift(1)
        r = np.log(X['1400'] / prev); s_ = np.sign(r)
        res = (s_ * np.log(X['1430'] / X['1400']) * 1e4).dropna()
        plac = (np.sign(np.log(X['1330'] / prev)) * np.log(X['1400'] / X['1330']) * 1e4).dropna()
        res = res[res.index >= '2010-06-01']; plac = plac[plac.index >= '2010-06-01']
        a_, b_ = res[res.index < '2018-01-01'], res[res.index >= '2018-01-01']
        an = b_.groupby(b_.index.year).mean()
        self.log(f'R {MERCADO} n {len(res)} todo {res.mean():+.2f} t {t_nw(res.values):.2f} | desc n {len(a_)} {a_.mean():+.2f} t {t_nw(a_.values):.2f} | conf n {len(b_)} {b_.mean():+.2f} t {t_nw(b_.values):.2f} anos+ {(an>0).mean():.2f}')
        self.log('A ' + MERCADO + ' ' + ' '.join(f'{k}:{v:+.1f}' for k, v in res.groupby(res.index.year).mean().items()))
        ab = r.abs().reindex(res.index); qq = pd.qcut(ab, 3, labels=False)
        self.log('T ' + MERCADO + ' ' + ' '.join(f'q{int(k)}:{v:+.2f}' for k, v in res.groupby(qq).mean().items()) + f' | placebo 13:30-14:00 {plac.mean():+.2f} t {t_nw(plac.values):.2f}')
        self.log(f'D {MERCADO} {res.index[0].date()} {res.index[-1].date()}')
