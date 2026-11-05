# PREREGISTRO C107 — Cereales en los días de informes del USDA (WASDE y existencias trimestrales) — 05-nov-2026

Redactado y subido a git ANTES de calcular. Fechas WASDE oficiales (esmis.nal.usda.gov, 2005-2026; `datos_c107_fechas_wasde.txt`).
Informes trimestrales de existencias/siembra (NASS): se aproximan como el último día hábil de marzo, junio y septiembre (en enero
coinciden con el WASDE). Todos se publican a las 12:00 ET, durante la sesión de cereales (09:30-14:20 ET).
Mecanismo: (A) prima por riesgo de anuncio (Savor-Wilson): quien mantiene la posición durante un informe que mueve mucho el precio
exige rentabilidad; (B) ajuste lento al dato en mercados menos seguidos que los macro de EE. UU.

## Datos
Futuros ZC (maíz), ZS (soja), ZW (trigo), Databento barras de 1 h (2010-06 → 2026-09, frontal; cambios de contrato excluidos), hora NY.

## Pruebas (3 mercados × 2 = 6)
- **A. Prima del día del informe:** largo del cierre de la barra de 13:00 del día hábil anterior al cierre de la barra de 13:00 del
  día del informe (≈ 14:00 a 14:00). Control: el mismo tramo los demás días.
- **B. Continuación tras el dato:** señal = signo de cierre(barra 12:00) / cierre(barra 11:00) el día del informe; posición en ese
  sentido del cierre de la barra de 12:00 al cierre de la barra de 13:00.
- Criterio (Bonferroni unilateral 0,05/6 → t ≥ 2,64): media > coste (ZC 3 pb, ZS 2,5, ZW 3,5) con t ≥ 2,64 y > 0 en 2010-17 y 2018-26;
  en A además mayor que el control (diferencia con t ≥ 2). Lo que pase se confirma con QuantConnect a 1 minuto. Contador +6.
