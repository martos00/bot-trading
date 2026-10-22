# Pre-registro B15 — Calendario × hora en 11 CFD de índices y petróleo (HistData) — 22-oct-2026
Redactado y enviado a git ANTES de calcular.
## Mercados (HistData M1, BID, EST → NY) y coste de CFD (ida y vuelta, fijado ahora)
GRXEUR (DAX) 1,0 · UKXGBP (FTSE) 1,5 · ETXEUR (EuroStoxx 50) 2,5 · FRXEUR (CAC) 2,0 · JPXJPY (Nikkei) 2,0 · AUXAUD (ASX 200) 1,5 · HKXHKD (Hang Seng)
3,0 · SPXUSD 1,0 · NSXUSD 1,0 · BCOUSD (Brent) 4,0 · WTIUSD 4,0 pb.
## Regla
Precio a cada hora en punto (NY) = cierre del minuto anterior (tolerancia 10 min). Franjas de 1 h (inicio 0-22, sin 16-18). Las mismas cuatro
familias de días que B14 (semana; D−2…D+2; PRE/POST/OPEX/POSTOPEX/D15; Q−2…Q+2) con sus n mínimos (200/80/60/25).
Descubrimiento 2010-2017; confirmación 2018 – 2026-09. Selección |t (NW)| ≥ 3,5; confirmación: t ≥ Bonferroni unilateral 0,05/k_sel; ≥ 60 % de
años; bruto ≥ 3 × coste.
## Aviso y requisito
Datos solo BID: los cambios de spread por hora pueden crear artefactos (B1). Comparar días distintos a la MISMA hora los reduce, pero no los
elimina (p. ej. festivos con spreads más anchos). **Todo lo que pase debe confirmarse con BID/ASK de Dukascopy en los días concretos** antes
de considerarse certificado. Contador + nº de reglas.
