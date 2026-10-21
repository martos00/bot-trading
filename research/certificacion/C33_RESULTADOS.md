# Resultados C33 — Ruptura del rango del día anterior y reversión post-noticia: NINGUNA CERTIFICADA

Pre-registro `PREREGISTRO_C33_ruptura_diaria_y_post_noticia.md`; script `c33_ruptura_noticias.py`; salida `c33_resultados.txt`.

## Aviso importante: la primera ejecución tenía un sesgo de simulación
En la primera versión, si a las 03:00 NY el precio ya estaba por encima del máximo de ayer (o por debajo del mínimo), la
compra (venta) se simulaba AL NIVEL de ruptura, más barato (caro) que el precio real. Resultado engañoso: +3,1 pb netos,
t 3,89, 7/8 años ("certificada"). Corregido: una orden stop se ejecuta a la apertura de la vela si esta ya supera el nivel.

| | 2012-2018 (neto) | 2019-2026 (neto) |
|---|---|---|
| R ruptura del día anterior (corregida) | −1,0 pb (t −1,56) | **−0,7 pb (t −0,87)**, 3/8 años; bruto +0,35 pb |
| N reversión después de noticias (08:45 → 10:00) | −0,3 pb | −0,7 pb, 2/8 años; bruto +0,2 pb |
Toda la "ventaja" de la ruptura venía del sesgo de ejecución. Lección añadida al método: en rupturas con órdenes stop, el
precio de entrada es max(nivel, apertura de la vela), nunca el nivel cuando el precio ya lo ha superado.
