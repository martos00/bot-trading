# Pre-registro C37 — Reversión del hueco de apertura en el S&P 500 (ES) — 21-oct-2026

Redactado y enviado a git ANTES de calcular nada con huecos de apertura (ES_1m de Databento ya descargado para C9; nunca
se ha medido con él el hueco 16:00 → 09:30).
## Fuente y mecanismo
Berkman, Koch, Tuttle y Zhang (JFQA 2012, "Paying attention: overnight returns and the hidden cost of buying at the
open"): la demanda minorista concentrada en la apertura eleva el precio de apertura y se revierte durante la sesión.
Práctica de mesa: "los huecos pequeños se cierran". En el proyecto solo se probó (H1) el fallo de huecos FUERA del rango de
ayer con 3 años de CFD; nunca el hueco en sí con 16 años de futuros.
## Regla (una sola versión)
- Datos: ES continuo por volumen (ES.v.0) en velas de 1 minuto, hora de Nueva York. Se excluyen los días en que el
  contrato del cierre de ayer y el de la apertura de hoy son distintos.
- Cierre de ayer C = cierre de la vela 15:59 (= 16:00) del día hábil anterior; apertura A = apertura de la vela 09:30.
- Hueco g = ln(A / C). Señal si 0,10 % ≤ |g| ≤ 1,00 %. Se opera EN CONTRA del hueco a la apertura A.
- Objetivo: C (orden límite; solo cuenta si el precio lo atraviesa en 1 tic). Stop de catástrofe a 2·|g| en contra de A
  (ejecución a max(stop, apertura de la vela) para no sesgar). Si no, salida al cierre de la vela 11:59 (12:00).
- Coste 1,5 pb por operación (1 tic de deslizamiento a la entrada + comisión; el CFD del US500 cuesta parecido).
## Tramos y criterios
Descubrimiento 2010-06 – 2017 (informativo). **Confirmación 2018 – 2026-09**: media neta > 0 con t (Newey-West) ≥ 2,0,
≥ 60 % de años positivos y bruto ≥ 3 × coste. Informativo: por tramos de hueco (0,1-0,3 / 0,3-0,6 / 0,6-1,0 %) y por
dirección. Sin cambiar umbrales, horario ni stop después de ver datos. Contador +1. Operable en CFD de FTMO (intradía).
