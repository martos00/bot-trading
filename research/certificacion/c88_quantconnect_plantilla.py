from AlgorithmImports import *
class GexGC(QCAlgorithm):
    def initialize(self):
        self.set_start_date(__INI__); self.set_end_date(__FIN__); self.set_cash(100000)
        self.f = self.add_future('GC', Resolution.MINUTE, extended_market_hours=False)
        self.universe_settings.resolution = Resolution.HOUR
        self.f.set_filter(0, 75)
        self.add_future_option(self.f.symbol, lambda u: u.strikes(-25, 25).expiration(0, 60))
        self.cierre = None; self.abierta = None; self.dia = None
    def on_data(self, data):
        hm = self.time.hour * 100 + self.time.minute
        fr = self.f.mapped
        if fr is None or fr not in self.securities: return
        p = self.securities[fr].price
        if hm == 1000 and self.dia != self.time.date() and self.time.weekday() < 5:
            self.dia = self.time.date()
            g = 0.0; n = 0
            for k, ch in data.option_chains.items():
                S = ch.underlying.price
                if not S: continue
                for c in ch:
                    if abs(c.strike / S - 1) > 0.10 or not c.open_interest: continue
                    gm = c.greeks.gamma
                    if gm is None or gm != gm: continue
                    g += (1 if c.right == OptionRight.CALL else -1) * c.open_interest * gm * S * S * 0.01; n += 1
            if n and self.cierre and p:
                s = 1 if p > self.cierre else -1
                self.abierta = (self.time.date(), fr, p, s, g)
        if hm == 1330:
            if self.abierta and self.abierta[0] == self.time.date() and p:
                d, sym, p0, s, g = self.abierta; p1 = self.securities[sym].price
                if p1: self.log(f'G {d:%y%m%d} {s:+d} {g:.2e} {math.log(p1 / p0) * 1e4:+.1f}')
                self.abierta = None
            self.cierre = p
