# Pre-registro E5 — E1 con órdenes limitadas (ejecución pasiva) — 22-oct-2026
Redactado y enviado a git ANTES de calcular nada. No cambia la ventaja (señal y horas de E1), solo cómo se entra y se sale.
## Regla
Días: laborables sin festivos TARGET (Año Nuevo, Viernes Santo, Lunes de Pascua, 1-may, 25/26-dic). FXCM M1 BID/ASK, hora de NY.
- **Entrada**: a las 06:00 NY, orden limitada de venta en L_e = ASK de cierre de la vela 05:59. Se considera ejecutada SOLO si en
  alguna vela 06:00–06:09 el BID máximo llega a ≥ L_e (el precio atraviesa la orden un spread entero: supuesto conservador).
  Si no, venta a mercado al BID de cierre de la vela 06:09.
- **Salida**: a las 07:50 NY, orden limitada de compra en L_x = BID de cierre de la vela 07:49. Ejecutada SOLO si en alguna vela
  07:50–07:59 el ASK mínimo llega a ≤ L_x. Si no, compra a mercado al ASK de cierre de la vela 07:59 (08:00).
- Comisión 0,45 pb ida y vuelta en todos los casos; deslizamiento 0,1 pb solo en las patas a mercado.
- **Referencia (E1 a mercado)**: venta al BID de 06:00 y compra al ASK de 08:00 (cierres de vela 05:59 / 07:59), 0,45 + 0,2 pb.
## Tramos y criterios
Descubrimiento 2012-2018; **confirmación 2019 – 2026-09**: (1) mejora media por operación (E5 neto − E1 neto) > 0 con t (NW)
≥ 2,0; (2) mejora positiva en ≥ 60 % de los años; (3) E5 neto > 0. Informativo: porcentaje de relleno pasivo en cada pata.
Si pasa, el EA usará la ejecución pasiva; si no, se queda a mercado. Contador +1.
