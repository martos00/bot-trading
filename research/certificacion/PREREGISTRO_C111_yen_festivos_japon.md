# PREREGISTRO C111 — USDJPY antes de los festivos de Japón (fixing de Tokio) — 06-nov-2026

Redactado y subido a git ANTES de calcular. Mecanismo: como en los días gotobi y a fin de mes (E9, E11, certificadas), las empresas japonesas
importadoras compran dólares en el fixing de Tokio (09:55 JST) para liquidar pagos; si el día siguiente es festivo en Japón (y laborable en
EE. UU.), los pagos se adelantan y se concentran en el último día hábil japonés antes del festivo. Gotobi (C10) era real 2003-2022 y se
apagó tras publicarse (2023): este efecto está relacionado y puede haberse apagado igual.

## Regla
Día D = día laborable en Japón cuyo siguiente día de lunes a viernes es festivo en Japón (paquete `holidays`, Japón; incluye Golden Week,
Obon NO (no es festivo oficial), fin de año 31-dic → 1/2/3-ene). Largo USDJPY de 08:00 a 09:55 JST del día D (en NY: 18:00/19:00 → 19:55/20:55
del día anterior según horario de verano; se convierte con zona horaria). Se excluyen los D que ya son día gotobi (5, 10, 15, 20, 25, fin de
mes) para medir solo el efecto del festivo; informativo con ellos.

## Datos y criterio
Principal: HistData USDJPY 1 min 2010-2026. Confirmación: FXCM USDJPY 1 min (2012-2026). Coste 0,8 pb (6J/MJY).
Pasa si: media > 0 con t (Newey-West) ≥ 2,24 en 2010-2026 en la principal; > 0 en 2010-17 y en 2018-26; ≥ 60 % de años positivos; media >
coste; confirmación FXCM media > coste con t ≥ 2,0; y > 0 desde 2023. Contador +1.
