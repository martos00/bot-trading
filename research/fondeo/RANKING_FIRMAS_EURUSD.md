# Ranking de firmas de fondeo para la estrategia EUR/USD (E1, riesgo 0,5%) — 21-oct-2026

Investigación de 16 firmas (3 búsquedas en paralelo, fuentes oficiales siempre que se pudo). Cálculo:
`ranking_firmas_eurusd.py` → `ranking_firmas_eurusd.txt` (backtest E1 2018-2026 con el coste de cada firma + Monte Carlo de
sus reglas). "Valor esperado" = P(superar) × [beneficio anual × capital × reparto × P(sobrevivir 1 año) + devolución] − precio.
Es una estimación orientativa: supone que la ventaja histórica se mantiene, y superar la evaluación lleva más de un año.

## Excluidas por no permitir bots que operen solos
Maven (prohíbe todo EA), Alpha Capital (solo EAs de gestión de riesgo), FundedNext (prohíbe EAs en cuentas ≥ 50.000 $),
Apex (futuros, prohíbe automatización). E8 no tiene evaluación de 2 fases (solo 1 fase con pérdida máxima dinámica del 4%).

## Ranking
Cifras recalculadas el 21-oct-2026 tras corregir el error de la σ de 60 días con huecos en E1 (ver
`../certificacion/E1_RESULTADOS.md`). El orden no cambia; todas mejoran ~0,6 puntos de rentabilidad anual.

| Firma | Comisión EUR/USD (fuente) | Coste/op | Neto anual | Supera | Valor esperado 1er año | Bots | Fiabilidad |
|---|---|---|---|---|---|---|---|
| Audacity Ability | 3 $ i/v (**terceros, contradictorio**; tabla oficial dice "por lado") | 0,52 pb | 7,4% | 79% | +3.977 $ | EA propio, VPS sí, mín. 2 min | Desde 2012; Trustpilot suspendido; reparto 75% |
| **FTMO 2-Step** | **2,50 $/lado = 5 $ i/v (oficial)** | 0,70 pb | 5,5% | 68% | +2.573 $ | **El más permisivo**; VPS sí | **Desde 2015, Trustpilot 4,8 (55k), compró OANDA** |
| Goat Funded Trader | 5 $ (sin aclarar lado) | 0,70 pb | 5,5% | 68% | +2.567 $ | EA propio con prueba; **sin VPS** | Trustpilot suspendido, 40% de 1 estrella |
| The5ers High Stakes | **4 $ i/v (oficial)** | 0,61 pb | 6,5% | 65% | +2.437 $ | Código propio; **una FAQ dice que prohíbe el trading algorítmico** | Desde 2016, Trustpilot 4,7; tope 4.000 $/pago |
| Blue Guardian | 5 $ (sin aclarar lado) | 0,70-1,14 pb | 0,8-5,5% | 37-62% | −103 a +2.337 $ | EA propio, VPS sí | Trustpilot suspendido |
| FundingPips | 5 $ (sin aclarar lado) | 0,70-1,14 pb | 0,8-5,5% | 41-71% | −303 a +2.363 $ | EA propio con prueba; **sin VPS** | Trustpilot 4,5 (71k) |
| FXIFY | 6 $ RAW / 0 $ All-In | 0,79 pb | 4,6% | 57-63% | +1.113 a +1.878 $ | EA con aprobación previa | Trustpilot 4,3 |
| Funded Trading Plus | 7 $ (terceros) | 0,87 pb | 3,6% | 48% | +602 $ | Sí | Trustpilot suspendido; límite 3% por símbolo |
| Topstep (futuro 6E) | 4,22 $ + 1 tick | 0,83 pb | 4,1% | 52% | +127 $ | Sí (API); sin VPS | Pérdida máxima trailing de 2.000 $ |

## Recomendación
- **FTMO 2-Step**: coste confirmado oficialmente, política de bots más clara y permisiva (VPS permitido, sin requisito de
  código propio ni aprobación), devuelve la evaluación con el primer pago, sin regla de consistencia en 2-Step y la firma más
  solvente. Su cuenta Swing evita además las restricciones de noticias y fin de semana en la financiada.
- **The5ers** tiene el coste oficial más bajo (4 $ i/v), pero exige confirmar por escrito que permite el bot (FAQ
  contradictoria) y limita los pagos a 4.000 $.
- **Audacity** sale primera solo porque su comisión de 3 $ i/v viene de terceros y su propia web dice "por lado": si fueran
  3 $ por lado (6 $ i/v), caería al nivel de FXIFY. Hay que verificarlo en su cuenta de prueba de spreads antes de considerarla.
- En todas, el coste real se mide en la demo con `MQL5/Scripts/Medir_Costes_EURUSD_0600_0800.mq5` antes de pagar nada.
