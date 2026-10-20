# Paso 2 — ¿Dónde se pueden operar las ventajas certificadas con un coste menor que la ventaja? (20-oct-2026)

Costes de fuentes de terceros (no verificados en una cuenta): las cifras de comisión discrepan entre fuentes y se dan
como rango. Salida del cálculo del EURUSD: `paso2_costes_eurusd.txt` (`paso2_costes_eurusd.py`, sobre la serie certificada
2018-2026; spread mediano medido a esas horas 0,16 pb; 1 lote ≈ 114.000 $, 1 pb = 11,4 $; deslizamiento 0,1 pb).

## EURUSD corto 06:00 → 08:00 ET (ventaja bruta 1,38 pb/día)
| Sitio (fuente de la comisión) | Coste i/v | Ventaja / coste | Neto | t neto | Sharpe anual neto | Años + |
|---|---|---|---|---|---|---|
| FundingPips, 2 $ i/v por lote (Benzinga, Investing) | 0,44 pb | **3,15** | 0,94 pb | 3,13 | 1,10 | 7/9 |
| FundingPips, 2,50 $ por lado | 0,70 pb | 1,97 | 0,68 pb | 2,26 | 0,79 | 6/9 |
| FTMO, 3 $ i/v (Investing, Propvator) | 0,53 pb | 2,62 | 0,85 pb | 2,84 | 1,00 | 7/9 |
| FTMO, 3 $ por lado (foro) | 0,79 pb | 1,75 | 0,59 pb | 1,96 | 0,69 | 6/9 |
| FundedNext, 5 $ i/v | 0,70 pb | 1,97 | 0,68 pb | 2,26 | 0,79 | 6/9 |
| FundedNext, 5 $ por lado | 1,14 pb | 1,21 | 0,24 pb | 0,80 | 0,28 | 6/9 |
| ECN minorista (IC Markets 7 $ i/v + 0,1 pip) | 0,88 pb | 1,57 | 0,50 pb | 1,67 | 0,59 | 6/9 |
| Futuros 6E en Topstep (1 tick + tasas 3,20 $ + 1 $) | 0,83 pb | 1,66 | 0,55 pb | 1,82 | 0,64 | 6/9 |

(El micro-futuro M6E es peor: su tick de 0,0001 ya cuesta ≈ 0,9 pb, más tasas.)
**Lectura:** sigue siendo positiva neta en todos los sitios; solo con el coste más bajo (FundingPips a 2 $ i/v) cumple la
puerta de costes del proyecto (ventaja ≥ 3 × coste). Con FTMO queda en 1,75-2,6 ×. **El dato decisivo es el coste real
en la cuenta concreta**, que hay que medir (comisión y spread a las 06:00 y 08:00 ET) en una demo.

## Cripto 21:00 → 23:00 UTC (ventaja bruta BTC 5,2 pb, ETH 6,85 pb)
| Sitio | Coste i/v aproximado | Ventaja / coste |
|---|---|---|
| FTMO (0,0325% por lado, blog oficial) | 6,5 pb + spread | < 1 |
| Kraken Prop (0,04% por lado) | 8 pb | < 1 |
| Binance futuros, órdenes límite (0,02% por lado, sin VIP) | ≈ 4 pb | 1,3-1,7 |
| Binance futuros, órdenes de mercado (0,05% por lado) | 10 pb | < 1 |
| MEXC 0% maker (solo web/app; por API 0,06%/0,08% desde jun-2026) | por API ≈ 14 pb | < 1 |
La franja no cruza los pagos de financiación de los perpetuos (00, 08 y 16 UTC). **Conclusión:** no hay ningún sitio de
fondeo donde sea operable; solo en un exchange con órdenes límite y con poco margen (y con capital propio, que no se usa
sin autorización del usuario). Queda aparcada.

## Decisión para el paso 3
Montar la estrategia sobre el **EURUSD**, con prioridad en la cuenta con menor coste real. Antes de dar por buena
ninguna cifra de coste, medirla en una demo/prueba gratuita de la firma elegida (requiere que el usuario la abra).
