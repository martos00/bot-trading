# PREREGISTRO C102 — Ruptura del rango asiático (regla C99) en otros futuros del CME ligados a Asia — 29-oct-2026

Redactado y subido a git ANTES de calcular. C99/C101: la regla funciona en oro y Nikkei (mercados con mucha actividad asiática) y no en
divisas europeas, plata, crudo ni S&P. Hipótesis: el rango fijado en Asia y roto en Europa/EE. UU. continúa en mercados donde Asia pesa.
Regla idéntica a C99. Mercados (5 pruebas): HG cobre, 6A dólar australiano, 6N dólar neozelandés, PL platino, PA paladio.

## Datos
Principal: Databento barras de 1 h (2010 → 2026-09, frontal, cambios de contrato excluidos). Aviso conocido: en barras horarias el stop
puede saltar en la barra de entrada y el objetivo no → sesgo en contra. Confirmación con 1 min donde exista: HistData AUDUSD (6A),
NZDUSD (6N). Informativo sin futuros del CME: Hang Seng (HKXHKD) y ASX 200 (AUXAUD) en HistData 1 min.
Costes (pb): HG 2,0; 6A 1,0; 6N 1,2; PL 3,0; PA 4,0.

## Criterio (Bonferroni unilateral 0,05/5 → t ≥ 2,58)
Principal: media > 0 con t (Newey-West) ≥ 2,58; ≥ 60 % de años positivos; > 0 en 2010-19 y 2020-26; media > coste. Confirmación (6A, 6N):
media > coste con t ≥ 2,0. HG, PL, PA sin segunda fuente: pasan como candidatas. Contador +5.
