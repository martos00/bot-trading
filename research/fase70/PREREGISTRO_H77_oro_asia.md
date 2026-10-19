# Pre-registro H77 — Deriva alcista del oro en horario asiático (hipótesis basada en literatura)

Redactado antes de descargar los datos de oro y de calcular ningún resultado.

## Fuente y nivel de evidencia
Donati & Jung (2019), *Gold Price Dynamics Around the Clock*, tesis de máster, Copenhagen Business
School (solo leído el resumen público): estacionalidad intradía "en forma de sombrero": el oro se
aprecia de forma robusta en horario oriental y se deprecia el resto del día. Estrategias con Sharpe
bruto de hasta 1,61; tras costes, "algo rentables". Contexto de mecanismo: Iwatsubo, Watkins & Xu (2018,
*J. Commodity Markets* 11) — operadores no informados dominan la sesión de Tokio, informados la de Nueva York.
**Nivel de evidencia bajo** (tesis de estudiantes, sin revisión por pares; reglas exactas no publicadas).
Por ser una regla propia derivada de una descripción cualitativa, exige **t ≥ 3** (umbral de
Harvey-Liu-Zhu para hipótesis nuevas).

## Regla (única, sin parámetros que optimizar)
- Cada día hábil de Tokio (lunes-viernes, sin festivos de Japón): **largo XAUUSD a las 09:00 de Tokio,
  cierre a las 15:00 de Tokio** (sesión de día de la Bolsa de Tokio / TOCOM). Sin stop ni objetivo.
- No cruza el rollover de las 17:00 ET: sin swap. No coincide con noticias de EE.UU. de alto impacto.

## Datos
HistData XAUUSD M1 (verificación previa de la zona horaria con el salto de las 08:30 ET) y ticks BID/ASK
de HistData en los meses del período fuera de muestra para medir el spread real en la entrada y la
salida. `calidad_datos` sobre las barras diarias.

## Tramos
**IS** hasta 2019-12 (período disponible para la tesis) y **OOS** 2020-01 → 2026-09.

## Costes
Ejecutable con ticks: compra al ASK de las 09:00 y venta al BID de las 15:00 (Tokio), más deslizamiento de
0,05 $/oz por lado. Estrés: el doble de deslizamiento.

## Criterios
Candidata si en el OOS, neta de costes ejecutables: media > 0 con **t ≥ 3**, positiva en ≥ 5 de 7 años y
mejor que una ventana de igual duración desplazada 12 horas (control de deriva general del oro, que ha
subido mucho en 2020-2026). Si cumple: simulación de fondeo (FTMO / FundedNext). N acumulado = 92.
