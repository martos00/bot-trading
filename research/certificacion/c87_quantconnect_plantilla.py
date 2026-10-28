from AlgorithmImports import *
TK, HS, MS = '__TK__', __HS__, __MS__
class Pin(QCAlgorithm):
    def initialize(self):
        self.set_start_date(__INI__); self.set_end_date(__FIN__); self.set_cash(100000)
        self.f = self.add_future(TK, Resolution.MINUTE)
        self.f.set_filter(0, 70)
        self.add_future_option(self.f.symbol, lambda u: u.strikes(-25, 25).expiration(0, 3))
        self.abierta = None; self.hechos = set()
    def on_data(self, data):
        hm = self.time.hour * 100 + self.time.minute
        if hm == 931 and self.time.date() not in self.hechos:
            for k, ch in data.option_chains.items():
                cs = [c for c in ch if c.expiry.date() == self.time.date()]
                if not cs: continue
                self.hechos.add(self.time.date())
                p0 = ch.underlying.price
                if not p0: continue
                oi = {}
                for c in cs:
                    if abs(c.strike / p0 - 1) <= 0.015: oi[c.strike] = oi.get(c.strike, 0) + (c.open_interest or 0)
                if not oi: self.log(f'SINOI {self.time.date()}'); continue
                kmax = max(oi, key=oi.get)
                if abs(kmax / p0 - 1) < 0.001: self.log(f'PEGADO {self.time.date()}'); continue
                self.abierta = (self.time.date(), ch.underlying.symbol, p0, kmax, 1 if kmax > p0 else -1)
        if hm == HS * 100 + MS and self.abierta and self.abierta[0] == self.time.date():
            d, sym, p0, k, s = self.abierta
            p1 = self.securities[sym].price
            if p1: self.log(f'R {d} {s:+d} {p0} {k} {p1} {s * math.log(p1 / p0) * 1e4:+.2f}')
            self.abierta = None
