# PREREGISTRO C80 — Deriva de la bolsa local antes de las decisiones del Banco de Japón, Banco de Inglaterra y RBA — 27-oct-2026

Redactado y subido a git ANTES de calcular. Pendiente n.º 5 del catálogo (Quantpedia 2025, "Pre-Announcement Drift for BoE, BoJ, SNB":
subida de la bolsa local en D−2 y D−1; para Australia y Canadá describen una deriva NEGATIVA). Mecanismo candidato: prima por
soportar el riesgo del anuncio (como la deriva previa al FOMC en EE. UU., que desapareció tras publicarse). Antecedente: C18 (bolsa
europea antes del BCE: candidata débil, t 1,59). Aviso: el estudio cubre 2010-2025, así que esto NO es una prueba posterior a su
publicación; como mucho dará una candidata que habría que vigilar en vivo.

## Fechas (descargadas de las webs oficiales el 27-oct-2026; `scratchpad/bc/*.csv`)
- **BoJ**: fecha de cada reunión según los ficheros de actas de boj.or.jp (2010-2026; incluye alguna reunión extraordinaria).
- **RBA**: decisiones de rba.gov.au 2010-2026; solo martes (se excluyen 2020-03-19, reunión extraordinaria, y 2026-06-03, dudosa).
- **BoE**: páginas "Monetary Policy Summary" de bankofengland.co.uk 2015-2026 (antes no están en ese formato); anuncio = primer jueves
  en o después de la primera fecha citada en la página (las reuniones terminan en miércoles y se anuncian el jueves a las 12:00).

## Regla
Bolsa local (CFD de HistData, hora de NY con cambio de hora, convertida a hora local): Nikkei JPXJPY al cierre de Tokio (15:00 JST),
ASX AUXAUD al cierre de Sídney (16:00), FTSE UKXGBP al cierre de Londres (16:30). D0 = día del anuncio (los tres anuncian durante la
sesión local). **Prueba principal: largo del cierre de D−3 al cierre de D−1** (los días D−2 y D−1). Días hábiles = días con precio de
cierre del propio mercado. Informativo: D0 (cierre D−1 → cierre D0).

## Criterio (3 pruebas)
- BoJ y BoE: signo previsto positivo. RBA: el signo lo fija 2010-2017 (|t| ≥ 2; si no, se cierra) y se confirma en 2018-2026.
- Pasa si (en la muestra completa para BoJ y BoE; en 2018-2026 para RBA) t (Newey-West) con el signo ≥ 2,13 (Bonferroni unilateral
  0,05/3), ≥ 60 % de años con el signo, y media > 6 pb en 2018-2026 (spread del CFD + 2 noches de financiación).
- Lo que pase → candidata (sin validación posterior a la publicación). Lo que falle → cerrado. Contador +3.
