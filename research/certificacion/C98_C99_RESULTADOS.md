# C98 y C99 — Resultados — 28-oct-2026
Preregistro commit c943007. Scripts `c98_hueco_cme_bitcoin.py`, `c99_ruptura_rango_asiatico.py`; salidas `c98_resultados.txt`, `c99_resultados.txt`.

## C98 — «El hueco del CME se cierra» (BTC, ETH; domingo 18:00 → lunes 16:00 NY): NO PASA, y pierde
| | n | Media | t | Huecos cerrados antes del lunes 16:00 / antes del viernes |
|---|---|---|---|---|
| BTC | 476 | **−32,5 pb** | −2,50 | 55 % / 79 % |
| ETH | 476 | −23,2 pb | −1,42 | 53 % / 76 % |
La creencia es cierta a medias: la mayoría de los huecos se cierran, pero los que no se cierran pierden mucho más. Lo contrario (seguir
el movimiento del fin de semana) ganó +32 pb en BTC; NO se adopta: sería una regla elegida tras ver los datos (requiere preregistro y
datos nuevos/forward).

## C99 — Ruptura del rango asiático (19:00-03:00 NY; ruptura 03:00-11:00; stop al otro extremo, objetivo 1× rango; cierre 16:45)
| | HistData M1 | Años + | 2010-19 / 2020-26 | Databento 1 h | Veredicto |
|---|---|---|---|---|---|
| **Oro** | **+3,58 pb (t 3,98)** | 12/17 | +2,61 / +4,98 | **GC +2,80 (t 3,11)** | **PASA** |
| EURUSD | +0,58 (t 1,32) | 11/17 | | 6E −1,46 | no |
| GBPUSD | +0,89 (t 2,12) | 13/17 | | 6B −0,02 | no |
| USDJPY | +2,05 (t 4,23) | 15/17 | +2,36 / +1,62 | 6J −0,97 (t −1,72) | no (no confirma) |
Aviso: en barras de 1 h el stop puede saltar en la barra de entrada y el objetivo no, lo que sesga la confirmación horaria a la baja
(más en divisas, con rangos estrechos). No cambia los veredictos fijados.

## Aporte a la cartera de futuros (informativo; `escenario_cartera_c93_c99.py`)
- Correlación C93-C99: 0,33. C99 sola: Sharpe 0,75 (contado) / 0,38 (GC 1 h).
- Con el tamaño estándar (0,5 % por operación) las dos del oro, al operar a diario, pesan demasiado y BAJAN el Sharpe de la cartera.
- Con tamaño reducido (15-40 % del estándar): firma normal sin euro 1,67 → 1,77-1,89; firma que permite mantener sin euro 2,10 → 2,15-2,22.
  Los pesos se han elegido sobre el mismo histórico: cifra optimista.
Contador +6.
