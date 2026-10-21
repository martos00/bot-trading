# Pre-registro E2 — Quitar a E1 los días sin flujo corporativo europeo o con noticia del BCE (21-oct-2026)

Redactado y enviado a git ANTES de calcular. E1 se ha analizado en conjunto, pero nunca separado por estos días.
Mecanismo de E1 (Breedon-Ranaldo): las empresas europeas compran USD en su horario laboral. Predicciones:
1. En **festivos europeos** (TARGET: 1-ene, Viernes Santo, Lunes de Pascua, 1-may, 25 y 26-dic; y festivos bancarios del
   Reino Unido, paquete `holidays`) el flujo no existe → el efecto debería ser ≈ 0.
2. En **días de reunión del BCE** (EA-MPD; decisión a las 13:45/14:15 CET, dentro o junto a la ventana 06:00-08:00 NY) el
   precio lo mueve la noticia → más ruido, sin más ventaja.
Regla E2 = E1 sin esos días (no opera). Todo lo demás idéntico (`e1_estrategia.construir`, coste 0,70 pb, riesgo 0,5%).

## Criterios
Muestra 2018-2026 (la de E1). (a) Efecto bruto 06-08 NY en los días excluidos: media sin significación o menor que en el resto
(se informa). (b) **E2 se adopta si su Sharpe neto es mayor que el de E1** y la diferencia de media diaria entre los días
excluidos y el resto es ≤ 0 (no se quitan días buenos). Contador +1 (N ≈ 1.790).
