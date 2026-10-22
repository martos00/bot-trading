# Pre-registro E7 — E1 el día después de un festivo europeo (flujo acumulado) — 22-oct-2026
Redactado y enviado a git ANTES de calcular nada para estos días.
## Hipótesis (derivada del mecanismo de E1)
Si el euro se debilita a las 06:00-08:00 NY por pagos en dólares de empresas europeas en días hábiles, el día hábil siguiente a un
festivo TARGET o del Reino Unido (sin flujo) acumula órdenes de dos días: el efecto debería ser mayor. Si se confirma, el EA podría
usar más riesgo esos días (≈ 8-10 días al año).
## Regla
Días "post": primer día hábil tras un festivo TARGET (1-ene, Viernes Santo, Lunes de Pascua, 1-may, 25/26-dic) o bancario del
Reino Unido (mismo calendario que E2). Lunes normales y resto de días como comparación. EURUSD FXCM M1 mid, corto 06:00→08:00 NY.
## Criterio (todo el periodo 2012-2026: con ~130 días no hay potencia para partir en tramos)
Diferencia (post − resto) > 0 con t de Welch ≥ 1,65 → se pre-registrará después una regla de tamaño para forward (no se cambia el
EA ahora). En otro caso, nada. Contador +1.
