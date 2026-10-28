# PREREGISTRO C90 — Bitcoin 21-23 UTC (C2, certificada) recortado a lo que se puede operar en el CME con una cuenta de fondeo de futuros — 28-oct-2026

Redactado y subido a git ANTES de calcular. Base: C2 (BTC largo 21:00 → 23:00 UTC; post-publicación 2022-02 → 2026-09 certificado con ETH).
Restricción: el CME cierra de 17:00 a 18:00 NY y las firmas de fondeo obligan a estar fuera antes de las 16:45-16:50 NY. La parte operable
de la ventana es:
- **Horario de verano de EE. UU.** (21-23 UTC = 17-19 NY): **22:00 → 23:00 UTC** (18:00 → 19:00 NY), domingo a jueves (fecha NY).
- **Horario de invierno** (21-23 UTC = 16-18 NY): **21:00 → 21:45 UTC** (16:00 → 16:45 NY), lunes a viernes.
Las horas las fija la plataforma, no los resultados. No se probará ningún otro recorte.

## Datos
Binance BTCUSDT 1 minuto (2022-02 → 2026-09: el periodo posterior a la publicación). Precio = apertura del minuto de cada hora.
Informativo: 2017-08 → 2022-01 con velas horarias solo para el tramo de verano (22-23 UTC).

## Criterio
Sobre 2022-02 → 2026-09: media > 0 con t (Newey-West) ≥ 2,0; ≥ 60 % de años positivos; media > 3 pb (coste estimado del micro
bitcoin MBT: ~1 tick + comisión sobre un contrato de 0,1 BTC). Informativo: neto con 1 pb (contrato grande BTC) y cada tramo por
separado. Pasa → candidata para la cuenta de futuros (otra fuente: ETH, como en C2). Contador +1.
