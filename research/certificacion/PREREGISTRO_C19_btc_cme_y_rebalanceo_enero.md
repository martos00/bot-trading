# Pre-registro C19 — Vencimiento del futuro de BTC en el CME y rebalanceo de enero en oro y plata (21-oct-2026)

Redactado y enviado a git ANTES de calcular ningún resultado (solo se descargaron los datos).

## V — Vencimiento mensual del futuro de bitcoin del CME (Blasco, Corredor y Satrústegui 2023; Quantpedia, datos a feb-2024)
Patrón descrito por Quantpedia (resumen del agente, no leído el original): día antes del vencimiento negativo, día del
vencimiento positivo, lunes siguiente positivo. Según el agente, el patrón cambió de signo tras el lanzamiento del ETF BITO
(oct-2021); por eso solo es limpio el período posterior a los datos de Quantpedia.
- Vencimiento: último viernes del mes (si no hay dato ese día, se omite). Velas diarias UTC de Yahoo `BTC-USD`.
- Regla compuesta: corto el jueves anterior + largo el viernes del vencimiento + largo el lunes siguiente (tres días UTC).
- Coste: 7 pb por ida y vuelta y por pata (comisión de cripto en fondeo, ver C2) → 21 pb por evento.
- Tramos: 2018-2021-09 (antes de BITO) y 2021-10 → 2024-02 informativos; **confirmación mar-2024 → sep-2026**.
- Criterios (confirmación): media neta > 0 con t ≥ 2,0 y bruta ≥ 3 × coste. Aviso: ≈ 31 eventos, potencia muy baja.

## E — Rebalanceo anual de los índices de materias primas (BCOM/GSCI) en enero (nota de práctica de JPMorgan vía Saxo)
Entre el 6.º y el 10.º día hábil de enero los fondos indexados devuelven los pesos a su objetivo. Sin los pesos objetivo
históricos (no gratuitos) se usa una aproximación declarada: si el metal subió el año anterior, su peso habrá crecido y se
venderá; si bajó, se comprará.
- Regla: oro (GC=F) y plata (SI=F), del cierre del 5.º al cierre del 10.º día hábil de enero; corto si la rentabilidad del
  año anterior fue > 0, largo si fue < 0. Media de los dos metales por año. Coste futuros ≈ 1 pb.
- Tramos: 2001-2014 y **2015-2026**. Criterios (confirmación): media > 0 con t ≥ 2,0 y positiva en ≥ 60% de los años.
  Aviso: 12 eneros, potencia muy baja.
Contador +2 (N ≈ 1.175).
