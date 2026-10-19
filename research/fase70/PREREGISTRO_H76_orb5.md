# Pre-registro H76 — ORB de 5 minutos (Zarattini & Aziz 2023, "Can Day Trading Really Be Profitable?")

Redactado antes de calcular.

## Fuente y evidencia previa
PDF del paper (SSRN 4416622) vía Wealth-Lab, leído. QQQ, 1-ene-2016 → 17-feb-2023: 25.000 $ → 192.806 $
(+675% neto de comisiones), alfa anual del 33%; sin deslizamiento ni spread. **Réplica independiente**
(blog MQL5, T.-P. Krueger, sep-2026; CFD de 5 índices 2015-2026): el bruto se reproduce (+0,13R en NQ),
pero el neto es ≈0 en todos los mercados.

## Reglas (literales del paper)
- Primera vela de 5 minutos (9:30-9:35 ET). Si cierra por encima de su apertura → largo; por debajo →
  corto; si apertura = cierre (doji, interpretación declarada: igualdad exacta al tick) → no se opera.
- Entrada en la apertura de la segunda vela (9:35). Stop: mínimo de la primera vela (largos) o máximo
  (cortos). R = |entrada − stop|. Objetivo 10R o cierre de sesión (16:00), lo que ocurra antes.
- Tamaño: unidades = entero(min(1% × capital / R, 4 × capital / entrada)). Capital inicial 25.000 $,
  con reinversión.
- Si en la misma vela de 1 minuto se tocan stop y objetivo, se asume el stop (conservador).
  Ejecución del stop al nivel del stop; si la vela abre más allá del stop (gap), a la apertura.

## Datos
HistData M1: NSXUSD (Nasdaq-100) como mercado principal (H76a) y SPXUSD (S&P 500) como réplica (H76b).
Hora NY con horario de verano (verificado en H69). Mismo control de calidad. Sesiones completas NYSE.

## Tramos
**IS** 2016-01 → 2023-02 (muestra del paper); **OOS hacia atrás** 2010-11 → 2015-12;
**OOS posterior a la publicación** 2023-03 → 2026-10.

## Costes (por ida y vuelta, en puntos del índice)
Paper: comisión despreciable. **CFD de prop firm:** NDX 1,5 pt y SPX 0,5 pt de spread + 1 tick de
deslizamiento en la salida por stop. Estrés: el doble. Se informan siempre el R medio bruto y neto.

## Criterios
Candidata si en el **OOS posterior a la publicación**, neto de costes de CFD: media > 0 en R con t ≥ 2,
y supera a la misma estrategia con dirección aleatoria (p < 0,05). Después: simulación de fondeo.
N acumulado = 91.
