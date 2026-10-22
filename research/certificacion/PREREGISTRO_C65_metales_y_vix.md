# Pre-registro C65 — ¿Los metales suben más antes del cierre cuando el VIX está alto? (volatilidad aplicada a E8/E10) — 22-oct-2026
Redactado y enviado a git ANTES de calcular.
Hipótesis: si la subida previa al cierre es cobertura ante el riesgo del cierre, debe ser mayor cuando el miedo del mercado es alto.
Régimen: VIX de cierre del día anterior (CBOE, VIX_History.csv) por encima / por debajo de su mediana de los 252 días previos.
Pruebas: (1) Oro, viernes 16:00 → 16:55 NY (GC 1 min, gc_vie); (2) Plata, víspera de festivo 16-17 NY (SI h1). Principal: diferencia de medias
(VIX alto − VIX bajo) en el oro > 0 con t de Welch ≥ 1,65. Informativo: la plata y la proporción media/desviación en cada régimen (lo que importa para
el tamaño). Si pasa, se pre-registraría en forward un tamaño mayor con VIX alto. Contador +1.
