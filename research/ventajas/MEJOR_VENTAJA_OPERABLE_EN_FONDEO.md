# ¿Cuál es la mejor ventaja real que se puede operar en una cuenta de fondeo? (20-oct-2026)

## 1. Las ventajas más fuertes del mercado tras 2012 (datos públicos de Kenneth French y AQR)
`mejores_ventajas_documentadas.py` → `mejores_ventajas_documentadas.txt` (factores mensuales, brutos, long-short):
| Ventaja | Sharpe 2012-2026 | t | ¿Operable en fondeo? |
|---|---|---|---|
| Baja beta global (BAB) | 1,16 | 4,43 | **No**: cartera larga-corta de cientos de acciones, apalancada y mantenida meses |
| Prima de mercado EE. UU. (comprar el índice) | 0,94 | 3,59 | **No**: caídas de −20% a −35% (2020, 2022) rompen la pérdida máxima del 10%; el swap de un CFD de índice largo cuesta ≈ 5-7%/año con los tipos actuales |
| Prima de mercado desarrollados | 0,79 | 3,02 | No (igual) |
| Baja beta EE. UU. | 0,75 | 2,88 | No (igual que BAB) |
| Momentum desarrollados | 0,50 | 1,90 | No: cientos de acciones, rotación mensual |
| Calidad, rentabilidad, value, inversión, tamaño | −0,16 a 0,42 | < 1,6 | No, y además débiles desde 2012 |
Estilos macro (value, momentum, carry en divisas, índices, materias primas y bonos; `research/fase71/aqr_cribado.txt`):
Sharpe 2012-2026 entre −0,6 y +0,45, ninguno con t ≥ 2.

## 2. Qué necesita una ventaja para ser operable en fondeo
1. Operaciones cortas (intradía): sin swap y sin huecos de fin de semana.
2. Instrumento muy líquido con spread mínimo (la ventaja por operación debe superar con margen el coste).
3. Cola izquierda pequeña: la pérdida diaria (5%) y la máxima (10%) se miden con la equity.
4. Un solo instrumento o pocos, disponibles como CFD o futuro en la firma, y que la firma permita bots.
Las grandes primas académicas fallan en 1, 3 y 4: son reales, pero son de carteras de acciones y de horizontes largos.

## 3. Lo que sí cumple los cuatro requisitos (probado en este proyecto)
| Ventaja | Estado | Neto tras costes de fondeo |
|---|---|---|
| **EUR/USD baja en la mañana/mediodía europeo** (C1 y sesión europea de C3; mecanismo de Breedon-Ranaldo) | **Certificada**: 3 fuentes de datos, 2010-2026, posterior a la publicación | Sharpe ≈ 0,7-1,1 según coste; 7-14%/año según riesgo; 2025-2026 negativos |
| GBP/USD en la sesión europea | Certificada | No diversifica (correlación 0,5 con EUR/USD) |
| Cripto 21-23 UTC | Certificada | **No operable**: comisión de las firmas (6,5-8 pb) > ventaja (5-7 pb) |
| Yen fuerte en horario de Tokio; dólar débil en horario de EE. UU. | Candidatas no certificadas | Solo verificables con datos futuros |
| ≈ 100 estrategias publicadas o populares (ORB, Noise Area, Connors, trend following, SMC, horarios...) | Descartadas | — |

## Conclusión
La mejor ventaja real operable en una cuenta de fondeo que se ha encontrado y certificado es la **venta de EUR/USD en la
mañana/mediodía europeo**. No es grande (≈ 1-2 pb por día antes de costes), pero es la única que cumple a la vez: evidencia
académica con mecanismo, persistencia tras la publicación, confirmación con datos independientes y compatibilidad con las
reglas de fondeo. Su punto débil es la debilidad de 2024-2026, que solo el forward en demo puede aclarar.
