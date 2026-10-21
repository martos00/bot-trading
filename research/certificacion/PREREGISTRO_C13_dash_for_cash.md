# Pre-registro C13 — "Dash for Cash" (Etula, Rinne, Suominen y Vaittinen, RFS 2020) en futuros del S&P 500 (21-oct-2026)

Redactado y enviado a git ANTES de calcular ningún resultado.

## Fuente (texto leído, versión de Aalto)
Muestra EE. UU. 1980-2013. Los pagos de fin de mes obligan a fondos e instituciones a vender acciones hasta el último día
de liquidación que garantiza el efectivo para el día T (último día hábil del mes); con liquidación a 3 días, T−3. Rentabilidad
anormal: −37 pb de T−8 a T−4 (presión vendedora) y +48 pb de T−3 a T+3 (reversión y entrada de dinero nuevo).
Regla de liquidación en EE. UU.: 3 días hasta el 5-sep-2017, 2 días hasta el 28-may-2024, 1 día después (la propia lógica
del artículo: la presión dura hasta el último día de liquidación; el artículo ya menciona el cambio de 2017).

## Regla (con s = días de liquidación vigentes en la fecha T)
- Corto del cierre de T−(s+6) al cierre de T−(s+1); largo del cierre de T−(s+1) al cierre de T+3. Con s = 3 es exactamente
  la ventana del artículo (rentabilidades T−8…T−4 y T−3…T+3). Una operación compuesta por mes.
- Datos: S&P 500 (^GSPC, cierres diarios Yahoo) como aproximación del futuro ES (declarada: el futuro descuenta tipo menos
  dividendo, pequeño en 12 días). Días = sesiones con dato.
- Coste (futuro ES): entrada, cambio de corto a largo y salida ≈ 2 idas y vueltas de 1 tick (12,5 $) + 4 $ sobre ≈ 250.000 $
  de nominal, más deslizamiento: **2,0 pb por mes**.

## Tramos y criterios
- Réplica 1990-2013 (dentro del artículo): media bruta > 0.
- **Confirmación 2014 → 2026-09** (después de su muestra), todos: (1) media neta por mes > 0 con t ≥ 2,0; (2) media bruta
  ≥ 3 × coste; (3) neta positiva en ≥ 60% de los años.
- Informativo: cada pata por separado; versión sin ajuste de liquidación (siempre s = 3); Nasdaq 100; correlación con E1.
Contador +1 (N ≈ 1.165). Si falla, se descarta sin cambiar ventanas.
