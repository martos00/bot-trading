# Pre-registro C50 — ¿El efecto de los metales crece con la duración del cierre? (dosis-respuesta) — 22-oct-2026
Redactado y enviado a git ANTES de calcular por categorías de cierre.
## Hipótesis
Si oro y plata suben la última hora (16-17 NY) por cobertura ante el periodo en que el mercado estará cerrado, el efecto debe crecer con la
duración del cierre: categoría 1 = lunes-jueves normales (pausa ~1 h); 2 = viernes normales (~49 h); 3 = víspera de festivo NYSE (cierre de
3 días o más, o festivo entre semana). Predicción: media(1) < media(2) < media(3) en GC y en SI.
## Datos y prueba
GC y SI futuro h1 (Databento), franja 16:00-17:00 NY, 2010-06 – 2026-09. Prueba principal: pendiente de la regresión de la rentabilidad sobre
la categoría (1, 2, 3), con errores de Newey-West, en la media de GC y SI (mismos días): pendiente > 0 con t ≥ 2,0. Informativo: medias por
categoría y mercado, y si 2 < 3 por separado.
## Uso
Si pasa: E8/E10 podrán pre-registrar un tamaño proporcional a la categoría (forward). Si no: nada cambia. Contador +1.
