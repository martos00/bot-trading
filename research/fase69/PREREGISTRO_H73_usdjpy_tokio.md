# Pre-registro H73 — Validación de costes y de datos de USDJPY-Tokio (ensayo de H71)

Redactado y enviado a git ANTES de descargar los datos de validación (Dukascopy).

## 1. Origen (sin selección nueva de reglas)

En H71 (pre-registro `PREREGISTRO_H71_fixings_fx.md`), uno de los 6 ensayos fijados de
antemano, **USDJPY-Tokio**, dio fuera de muestra (2020-2026, HistData BID):
+4,00 pb/día bruto, t=5,5, SR 2,05; con spread fijo de 1,0 pip por tramo, +2,48 pb/día,
t=3,4. La hipótesis principal de H71 (EURUSD-Europa) falló y queda descartada; este
resultado **no la rescata**. H73 evalúa la **misma regla, sin ningún cambio**, como
candidata independiente. Con Bonferroni sobre 81 ensayos, t=5,5 sigue siendo significativo
(p ajustado < 1e-5). No se añade ensayo nuevo al contador (N = 81) porque la regla y el
par ya estaban pre-registrados; cualquier variante (p. ej. solo el tramo 1, otra hora
de entrada) contaría como ensayo nuevo y **no se adopta en esta fase**.

Regla congelada: día = fecha de Tokio (lunes-viernes, sin festivos de Japón). Tramo 1: largo
USDJPY de 17:05 ET del día anterior a 09:55 Tokio (fixing). Tramo 2: corto USDJPY de 09:55
Tokio a 08:00 Frankfurt. Sin swap (no cruza las 17:00 ET).

Contexto documental: Krohn-Mueller-Whelan (2024) ya señalan que el yen es la divisa con la
reversión de Tokio más fuerte (1 USD → 12,2 USD en 1999-2019, bruto). Existe literatura
sobre el sesgo del fixing de Tokio por compras de dólares de importadores japoneses
(efecto "gotobi", días 5, 10, 15, 20, 25 y fin de mes); se citará solo lo que se lea.

## 2. Riesgo que se quiere descartar

La entrada a las 17:05 ET coincide con el rollover, cuando el spread se amplía. Si el BID
está temporalmente deprimido, "comprar al BID de HistData" sobrestima la rentabilidad.

## 3. Datos de validación (fijados)

Dukascopy, ticks BID/ASK (ficheros horarios), USDJPY. Muestra: el primer día de Tokio
válido de cada mes, ene-2020 → sep-2026. En cada día: mid y spread en los 4 instantes
(último tick en los 5 minutos anteriores).

## 4. Criterios

1. **Datos:** en los días de la muestra, la correlación entre la rentabilidad diaria bruta de
   HistData (BID) y la de Dukascopy (mid) ≥ 0,9, y diferencia media |HistData − mid| <
   0,5 pb/día. Si falla, el resultado de H71 se considera artefacto y H73 se cierra.
2. **Coste realista:** spread medido (mediana de la muestra en cada instante) + comisión ECN
   0,35 pb/lado + deslizamiento 0,1 pb/lado. Neto OOS 2020-2026 > 0 con t ≥ 2 y positivo en
   ≥ 4 de los 7 años.
3. **Estrés:** con el percentil 90 del spread en cada instante, neto OOS > 0 (se informa;
   si falla, la estrategia se declara frágil a costes).
4. Diagnósticos que se informan pero **no** se usan para elegir reglas: tramo 1 frente a
   tramo 2; días gotobi frente al resto; spread por instante.

Si 1-2 se cumplen: congelar especificación, calcular riesgo/capital, EA para MT5 y propuesta
de forward test en demo, con una comprobación previa del spread real del bróker del usuario
a las 17:05 ET.
