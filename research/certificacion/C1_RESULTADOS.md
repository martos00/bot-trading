# Certificación C1 — EURUSD corto 06:00 → 08:00 ET: RESULTADOS

## Preliminar (20-oct-2026): 2.157 días de FXCM + 126 de Dukascopy (descarga de huecos aún en curso)
Salida: `c1_resultados_preliminar.txt`. Criterios del pre-registro sin cambios.

| Criterio | Resultado | |
|---|---|---|
| C1 punto medio, corto 06→08 ET, 2018-2026 | 2.178 días, **1,39 pb/día, t = 4,59** (solo FXCM: 1,40 pb, t = 4,61) | Cumple |
| C2 años positivos | 2018 1,34 · 2019 1,76 · 2020 0,07 · 2021 1,44 · 2022 3,73 · 2023 1,95 · 2024 0,58 · 2025 1,26 · 2026 −0,84 → **8/9** | Cumple |
| C3 concordancia con HistData | correlación 0,922, diferencia de medias −0,06 pb | Cumple |
| C4 punto medio − BID | +0,000 pb; spread mediano 0,17 pb a las 06:00 y a las 08:00 | Cumple |

Informativo: GBPUSD corto 06→08 (HistData) 1,03 pb, t = 2,75 (coherente con el mecanismo de Breedon-Ranaldo);
franjas 05→07 0,50 pb (t 1,81), 07→09 0,15 pb (t 0,38), 06→07 0,46 pb (t 2,41), **07→08 0,92 pb (t 4,20)**: el efecto se
concentra en la hora 07-08 ET. Señal de alerta: 2024 (0,58) y 2026 (−0,84) más débiles.

**Veredicto preliminar: cumple los cuatro criterios.** Se confirmará con los 120 días de huecos rellenados.

## Final (20-oct-2026): 2.201 de 2.283 días hábiles
Salida: `c1_resultados.txt`. La descarga de huecos de Dukascopy se detuvo por límite de tiempo (el servidor limita la
frecuencia): se completaron 38 de los 120 días sin FXCM; quedan **82 días sin dato** (12 de 2025 y 70 de 2026), por
disponibilidad de la fuente, no por nada relacionado con los precios.

| Criterio | Resultado | |
|---|---|---|
| C1 | **1,38 pb/día, t = 4,59** | Cumple |
| C2 | 8/9 años positivos (2025: 1,23; 2026: −0,84, con solo ≈ 124 días de dato) | Cumple |
| C3 | correlación 0,924 con HistData, diferencia de medias −0,06 pb | Cumple |
| C4 | punto medio − BID = 0,000 pb; spread mediano 0,17 pb | Cumple |
| C5 | mecanismo publicado (Breedon-Ranaldo 2013) | Cumple |

Informativo: la ventaja se concentra entre las 07:00 y las 08:00 ET (0,96 pb, t = 4,37); GBPUSD también baja en la franja
(t = 2,75), coherente con el mecanismo.

## Veredicto: VENTAJA CERTIFICADA (bruta)
EURUSD baja de media 1,38 pb entre las 06:00 y las 08:00 ET (mediodía europeo), en tres fuentes de datos (HistData, FXCM,
Dukascopy), descubierta en 2010-2017 y confirmada en 2018-2026, posterior a su publicación académica.
Avisos para el paso 2: el tamaño es pequeño (1,38 pb) frente a costes habituales (spread ≈ 0,17 pb + comisión típica
≈ 0,6-0,7 pb ida y vuelta) y 2024/2026 son los años más débiles.
