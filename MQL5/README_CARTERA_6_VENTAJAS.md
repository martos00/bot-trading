# Cartera CFD (EA `Cartera_6_Ventajas_EA.mq5`, versión del 12-nov-2026)

Versión actualizada con los costes medidos en **Upcomers** (`research/costes_cfd/upcomers_*.csv`) y **FTMO** (`ftmo_*.csv`).
Backtest de esta cartera con costes de Upcomers (`research/certificacion/cartera_cfd_upcomers.py`): Sharpe 1,82 sin bitcoin y con oro a las 16:45; con bitcoin y oro 16:55 (C116) 2,24: riesgo 0,5 % → 13,8 %/año, caída −6,0 %; riesgo 0,65 % → 18,0 %/año, caída −7,8 %. Antes:
riesgo 0,5 % → 11,0 %/año (al 60 % ≈ 6,6 %), caída máx. −9,0 %; riesgo 0,65 % → 14,2 %/año, caída −11,7 %. Bitcoin no está en esa cifra.

## Instalación
1. Copia `Experts/Cartera_6_Ventajas_EA.mq5` a `MQL5/Experts` de tu MT5, ábrelo en MetaEditor y compila (F7). Si sale algún error, mándamelo.
2. **Herramientas > Opciones > Gráficos > Máx. barras en ventana = Unlimited** (la sigma usa hasta 250 días de velas M1).
3. Abre un gráfico **M1** de XAUUSD, USDJPY, EURJPY, GBPJPY, JPCJPY.c y BTCUSD.nx y retrocede unos meses para que descargue historial.
4. Pon el EA en **un solo gráfico** (cualquiera) y activa **Algo Trading**. La cuenta tiene que ser de **cobertura (hedging)**: el EA avisa si no.
5. Revisa la pestaña Expertos: debe decir «Cartera CFD iniciada… Servidor invierno UTC+1» (Upcomers) o UTC+2 (FTMO).

## Parámetros que hay que mirar
| Parámetro | Upcomers Horizon | Upcomers Odyssey | FTMO |
|---|---|---|---|
| `InpRiesgoPct` | 0,5 | 0,5–0,65 | 0,5–0,65 |
| `InpPerdidaDiariaMaxPct` | 2,5 (regla 3 %) | 3,5 (regla 4 %) | 4 (regla 5 %) |
| `InpPerdidaTotalMaxPct` / `InpPerdidaTotalArrastre` | 5,5 / true | 9 / false | 9 / false |
| `InpPerdidaMaxOperacionPct` | 1,4 (regla 1,5 %) | 0 o 1,4 | 0 |
| Nikkei / bitcoin | `JPCJPY.c` / `BTCUSD.nx` | igual | `JP225.cash` / `BTCUSD` (en FTMO bitcoin **no** compensa: desactívalo) |
| `InpNikkeiCierreViernes` | 1555 | 1555 | revisar |

- `InpModo` = EXAMEN con `InpMultExamen` = 1 → mismo riesgo en examen y en fondeada.
- `InpFestivosNYSE` trae 2025-2027.
- `InpSoloDemo` = false: las cuentas de las prop firms suelen ser demo, pero así el EA no se bloquea si la cuenta figura como real.

## Estrategias (hora de Nueva York)
| Estrategia | Símbolo | Días | Entrada → salida | Peso |
|---|---|---|---|---|
| E8 | XAUUSD largo | viernes | 16:00 → 16:55 (`InpE8_Salida`; en FTMO 1645) | 1 |
| E9 | USDJPY largo | antepenúltimo laborable del mes | 07:00 → 08:00 | 1 |
| E11 | USDJPY+EURJPY+GBPJPY corto | último laborable de mar/jun/sep/dic | 00:30 → 02:00 | 1/3 cada uno |
| E15 | XAUUSD corto | antepenúltimo laborable del mes | 09:30 → 10:00 | 1 |
| E13 | Nikkei largo | 2.º laborable de ene/abr/jul/oct | 15:00 → 16:00 | 1 |
| E16 | Nikkei corto | penúltimo laborable de mar/jun/sep/dic | 20:00 → 21:00 | 1 |
| C93 | XAUUSD | laborables | ruptura del máx./mín. de la sesión anterior entre 08:00 y 15:00; stop 1 ATR(14), objetivo 3 ATR; salida 16:45 | 0,2 |
| C99 | XAUUSD | laborables | ruptura del rango 19:00–03:00 entre 03:00 y 11:00; stop en el otro extremo, objetivo 1 anchura; salida 16:45 | 0,2 |
| C101 | Nikkei | laborables | igual que C99 (el viernes sale a las 15:50 por el cierre del Nikkei) | 0,2 |
| Bitcoin | BTCUSD largo | laborables | 21:00 → 23:00 **UTC**; no entra si el spread > 1,5 pb | 0,2 |

Desactivadas: E2 euro (quitado de la cartera), E10 plata y plata (spread 7–14 pb), E12 cesta, E14 FTSE, C113 oro Asia (pendiente de comprobar en CFD).

## Cómo funciona
- **Tamaño** = riesgo × peso / sigma de la franja (la mayor de 60 y 250 días) × escala de volatilidad, con tope de exposición después de la escala.
  Si el broker no tiene historial suficiente, usa la sigma típica ×1,3 y avisa (`aviso_sigma_respaldo_sin_historico`).
- **Control de volatilidad**: al cerrar cada sesión (17:00 NY) guarda el resultado en `Cartera_CFD_pnl_diario.csv` **dividido por la escala** en vigor;
  a partir de 40 sesiones la escala = 0,35 % ÷ desviación de las últimas 60 (entre 0,5 y 2). **No borres ese archivo.**
- **Stops**: franjas, stop de catástrofe a 4 sigmas recortado para no perder más de `InpPerdidaMaxOperacionPct`; rupturas, el stop de la regla
  (si la pérdida pasaría del máximo, se reducen los lotes, no se mueve el stop).
- **Pausas de sesión**: cierra 5 min antes de cualquier pausa de más de 30 min (o del fin de semana en las de varias noches);
  no entra si la sesión no cubre al menos el 75 % de la franja.
- **Avisos** con sonido (y al móvil con `InpNotificacionesMovil`): errores, paradas, stops de catástrofe, falta de historial, símbolo no encontrado.
- **Registro**: `MQL5/Files/Cartera_CFD_log.csv`. Mándamelo cada semana las primeras semanas.
