# Guía: backtest en NinjaTrader, medir costes y demo de varios meses

## Paso 1 — Compilar
1. Copia `Strategies/CarteraFuturosB.cs` en `Documentos\NinjaTrader 8\bin\Custom\Strategies\`.
2. NinjaTrader → New → NinjaScript Editor → F5. Mándame los errores tal cual (texto o captura) hasta que compile sin errores.

## Paso 2 — Backtest en NinjaTrader (Strategy Analyzer)
Objetivo: comprobar que el bot hace en NinjaTrader las mismas operaciones que el backtest de Python. No sustituye al de Python
(que ya está validado); sirve para encontrar errores del bot.
1. Datos: hace falta historia de 1 minuto de cada contrato. La da la conexión de datos (demo de NinjaTrader/Tradovate o la de la
   firma). Conecta primero y deja que descargue.
2. New → Strategy Analyzer → estrategia CarteraFuturosB:
   - Contratos: para backtest usa los **continuos**, p. ej. `MGC ##-##`, `SIL ##-##`, `MJY ##-##`, `MHG ##-##`, `NKD ##-##`
     (Tools → Options → Data → «Merge policy: Merge back adjusted»).
   - **Operar también en el histórico = true** (si no, en el backtest no opera).
   - Fechas: los últimos 6-12 meses (lo que tenga la conexión).
   - Modo, riesgo y capital como vayas a operar (p. ej. B, 0,65 %, 150000; bitcoin y cesta E12 desactivados).
   - Comisiones: plantilla con la comisión de la firma por contrato micro (pregúntala; si no la sabes, 1 $ por lado).
   - Slippage: 1 tick.
3. Ejecuta y exporta:
   - Pestaña **Trades** → clic derecho → Export → CSV.
   - El registro del bot: `Documentos\NinjaTrader 8\CarteraFuturos\CarteraFuturos_log.csv`.
4. Mándame los dos archivos. Repito ese mismo periodo en Python con los datos que tengo y comparo operación por operación:
   mismos días, mismas horas, mismo sentido y tamaños parecidos. Si algo no cuadra, corrijo el bot.

## Paso 3 — Medir los costes reales
El bot ya apunta en el registro cada ejecución:
`ejecucion | contrato | fill_compra_desliz_X_ticks_Y_pb_comision_Z` = cuánto peor (o mejor) fue el precio frente al precio en el
momento de decidir, y la comisión.
- En el backtest los costes son supuestos (oro 0,74 pb, plata 2,3 pb, yen ~0,5 pb por ida y vuelta).
- En la demo veremos el coste real a las horas del bot (sobre todo viernes 16:00-16:57 en oro y plata).
- Ojo: en una cuenta de simulación las ejecuciones son simuladas (suelen ser algo optimistas). El coste definitivo se ve en la
  primera cuenta de fondeo real. Pide también a la firma su tabla de comisiones.

## Paso 4 — Demo de varios meses
1. **Datos en tiempo real del CME en una cuenta de simulación** (imprescindible). Opciones:
   - Prueba gratuita de datos de NinjaTrader/Tradovate (suele ser de 14 días; después, suscripción de datos).
   - Opción práctica: un examen barato de la firma (p. ej. el de 1 paso de Elite Trader Funding, ~35 $/mes) funciona como demo
     con datos reales y con las reglas de la firma. **Solo después de que aprueben el bot por escrito.**
2. **Ordenador siempre encendido** o VPS (si la firma lo permite):
   - Opciones de energía: nunca suspender ni apagar el disco.
   - Windows Update: horas activas / reinicio programado fuera de los viernes 15:00-23:30 hora de España.
   - NinjaTrader: Tools → Options → General → «Auto-connect» y conexión a la cuenta al arrancar.
   - Imprescindible conectado: viernes de 16:00 a 17:00 NY (22:00-23:00 en España), vísperas de festivo de EE. UU., los dos
     últimos días hábiles de cada mes y el último del trimestre de madrugada (yen 00:30-02:00 NY = 06:30-08:00 en España).
3. **No reinicies la estrategia con posiciones abiertas** (el bot no las reconoce). Si hay que reiniciar, hazlo cuando esté plano.
4. **Cambio de contratos** (rollover): oro y plata cada 2 meses, cobre, Nikkei y yen cada trimestre. La semana anterior al
   vencimiento cambia el contrato en la estrategia (desactivar, cambiar, activar, estando plano).
5. **Cada semana o cada dos**, mándame:
   - `CarteraFuturos_log.csv` y `CarteraFuturos_pnl_diario.csv`.
   - Si puedes, Account Performance → Executions exportado a CSV.
   Yo compruebo: que entró en todas las ventanas que tocaba (y por qué no si no lo hizo), el coste por operación, y el resultado
   frente a lo esperado.
6. **Cuánto tiempo:** 2-3 meses para comprobar que funciona sin fallos y medir costes (~30-40 operaciones). Para estimar el Sharpe
   real hacen falta muchos más meses: eso lo iremos viendo con las primeras cuentas reales pequeñas.

## Criterios para pasar a cuentas de fondeo
- 0 fallos técnicos graves en el último mes (entradas y salidas a su hora, sin posiciones olvidadas).
- Coste medio por operación ≤ 1,5 × el supuesto del backtest.
- Resultado de la demo no claramente negativo (con tan pocas operaciones, el resultado aún dice poco).
