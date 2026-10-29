# Bot de la cartera de futuros (NinjaTrader 8) — `Strategies/CarteraFuturosB.cs`

Estrategia de NinjaScript con la cartera de `research/CARTERA_FUTUROS.md`. Por defecto es el **modo B** (completa). El **modo A** sirve
para las firmas que obligan a cerrar a las 16:45 NY: quita la plata del viernes, la cesta de materias primas en víspera de festivo y
bitcoin, y saca el oro del viernes y la plata de víspera a las 16:45.

**No se ha compilado** (no hay NinjaTrader aquí). Compílalo y pásame los errores del NinjaScript Editor tal cual.
**Por defecto solo opera en cuentas de simulación** (las que empiezan por "Sim" o "Playback").

## Estrategias que lleva (horas de Nueva York)
| Nombre en el registro | Mercado | Regla | Modo |
|---|---|---|---|
| E8_oro_viernes | MGC | viernes, largo 16:00 → 16:55 (A: 16:45) | A y B |
| E15_oro_Dmenos2 | MGC | antepenúltimo laborable del mes, corto 09:30 → 10:00 | A y B |
| C93_oro_dia_anterior | MGC | rompe el máx./mín. de la sesión anterior entre 08:00 y 15:00; stop 1 ATR, objetivo 3 ATR; sale 16:45 | A y B |
| C99_oro_rango_asia | MGC | rompe el rango 19:00-03:00 entre 03:00 y 11:00; stop al otro lado, objetivo 1 rango; sale 16:45 | A y B |
| C102_cobre_rango_asia | MHG | igual que C99 | A y B |
| C101_nikkei_rango_asia | NKD | igual que C99 | A y B |
| E13_nikkei_Qmas2 / E16_nikkei_Qmenos2 | NKD | 2.º laborable del trimestre largo 15-16; penúltimo del trimestre corto 20-21 | A y B |
| E9_yen_fin_mes / E11_yen_fin_trim | MJY | antepenúltimo laborable del mes corto 07-08; último del trimestre largo 00:30-02:00 | A y B |
| E10_plata_vispera | SIL | víspera de festivo NYSE, largo 16:00 → 16:55 (A: 16:45) | A y B |
| plata_viernes | SIL | viernes, largo 16:30 → 16:59 | solo B |
| E12_cesta_* | 12 materias primas | día anterior a la víspera, largo 13:55 → 13:55 del día siguiente | solo B |
| bitcoin_21_23_UTC | MBT | laborables, largo 21:00 → 23:00 UTC | solo B (requiere que el CME negocie cripto entre 17 y 18 NY; si no hay precio, no entra) |

## Capital: el punto más importante
Con contratos enteros, cada estrategia necesita un capital mínimo para operar al menos 1 contrato con el riesgo del backtest
(0,5 % por operación; las diarias, 0,1 %). Estimación con precios de 2025-26:

| Estrategia | Capital mínimo aprox. |
|---|---|
| Yen (E9, E11) | 1.000-2.500 $ |
| Oro viernes (E8) | 7.000 $ |
| Oro D-2 (E15) | 15.000 $ |
| Plata viernes / víspera | 17.000 / 26.000 $ |
| Bitcoin (MBT) | 40.000 $ |
| Cobre rango asia (C102) | 75.000 $ |
| Nikkei Q+2 / Q-2 (NKD, 5 $ × índice ≈ 318.000 $ por contrato) | 87.000 / 176.000 $ |
| Oro del vídeo C93 / oro rango asia C99 | 200.000 / 250.000 $ |
| Nikkei rango asia C101 | ~900.000 $ |
| Cesta E12 (12 futuros grandes) | > 1.000.000 $ |

Sharpe de lo que se puede operar (2018-2026, con control de volatilidad; `research/CARTERA_FUTUROS.md`):
- Cuenta de 50.000 $: A 1,85 · **B 2,33** (caída al 25 %: 10,3 %).
- Cuenta de 100.000-150.000 $: A 1,95 · **B 2,48** (caída al 25 %: 11,3 %).
- Cuenta de 300.000 $: A 2,11 · B 2,55.

Lo que no llega a 1 contrato se registra como `sin_entrada_0_contratos` y no se opera.

## Configuración para Tradeify (la firma que mejor encaja con B hoy, sin confirmar)
Según sus propias páginas (oct-2026): cierre obligatorio 16:59 NY (12:59 en días de cierre anticipado), sin cripto; bots propios con
prueba de autoría según terceros. Configuración: Modo = B_completa, Operar bitcoin = false, Operar cesta E12 = false, salida de la plata
del viernes = 1657. Cuenta de 50.000 $: Sharpe 2,22 con control de volatilidad (A con cierre 16:45: 1,85). Confirmar por escrito antes.
**Ojo:** en días de cierre anticipado (12:59) el bot no conoce la regla de la firma; la víspera de festivo la plata entra a las 16:00:
si la firma cierra a las 12:59 ese día, desactiva E10 a mano o el bot no entrará si la sesión del CME cierra antes.

## Instalación
1. Copia `CarteraFuturosB.cs` en `Documentos\NinjaTrader 8\bin\Custom\Strategies\`.
2. En NinjaTrader: New → NinjaScript Editor → pulsa F5 (compilar). Mándame cualquier error.
3. Datos en tiempo real del CME en una cuenta de simulación. Opciones: la demo de NinjaTrader/Tradovate, la demo de Rithmic que dan
   las firmas, o una prueba gratuita de una firma. Sin datos en tiempo real el bot no puede operar.
4. Tools → Options → General → zona horaria: la que uses. El bot convierte a la hora de Nueva York por su cuenta.
5. Abre un gráfico de 1 minuto de **MGC** (el contrato actual) y añade la estrategia CarteraFuturosB (o desde la pestaña Strategies).
   - Days to load: **150** como mínimo (necesita 60 días de historia para el tamaño y 15 sesiones para el ATR).
   - Account: **Sim101** (o la cuenta de simulación que uses).
   - Contratos: escribe el **vencimiento actual** de cada mercado (p. ej. `MGC 12-26`). **Cámbialos al vencer** (oro, plata y cobre:
     cada 2 meses; bitcoin: cada mes; Nikkei y yen: cada trimestre). Si un contrato no existe, NinjaTrader avisa al cargar.
   - Capital (USD): 0 = saldo de la cuenta; en una cuenta de fondeo pon el tamaño de la cuenta (p. ej. 50000).
   - Festivos NYSE: ya lleva 2026 y 2027; ampliar cada año.
6. Activa la estrategia (Enabled). El PC/VPS tiene que estar encendido: los stops los vigila el bot, no el servidor.

## Registro (lo que tienes que mandarme)
`Documentos\NinjaTrader 8\CarteraFuturos\CarteraFuturos_log.csv`: cada entrada, salida y motivo (también por qué no entró).
`CarteraFuturos_pnl_diario.csv`: resultado de cada día (lo usa el control de volatilidad a partir de 40 días).

## Diferencias conocidas con el backtest
- El tamaño usa la sigma de los últimos 60 laborables de la franja (el oro del viernes, de todos los días y no solo de los viernes).
- Las rupturas entran a mercado al tocar el nivel; en el backtest, al nivel exacto. Puede costar algo de deslizamiento.
- No hay filtro de noticias (NinjaTrader no trae calendario).
- Si reinicias la estrategia con posiciones abiertas, el bot no las reconoce: ciérralas a mano antes de reiniciar.
- Las posiciones de varias estrategias en el mismo mercado se netean (solo se envía la diferencia).
