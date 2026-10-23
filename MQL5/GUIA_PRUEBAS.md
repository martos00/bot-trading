# Guía para probar el bot (cartera de 6 ventajas)

Orden: **0 preparar → 1 medir costes → 2 backtest en MT5 → 3 demo en tiempo real → 4 decidir**. No se arriesga dinero en ninguna de estas fases.

## Fase 0 — Preparar (10 minutos)
1. Descarga del repositorio estos tres archivos:
   - `MQL5/Scripts/Comprobar_Cuenta_y_Costes_6_Ventajas.mq5`
   - `MQL5/Experts/Cartera_6_Ventajas_EA.mq5`
   - `MQL5/README_CARTERA_6_VENTAJAS.md` (detalle de parámetros)
2. En MT5: *Archivo → Abrir carpeta de datos* → copia el script en `MQL5/Scripts` y el EA en `MQL5/Experts`.
3. Abre MetaEditor (F4), abre cada archivo y pulsa **Compilar (F7)**. Si sale algún error, mándame el texto exacto.
4. Usa una cuenta **demo** (la prueba gratuita de FTMO o la demo de MetaQuotes). Mejor la de FTMO: tiene sus spreads y su horario.

## Fase 1 — Medir costes en tu cuenta (15 minutos, una vez)
1. Abre un gráfico **M1** de cada símbolo (EURUSD, USDJPY, EURJPY, GBPJPY, XAUUSD, XAGUSD, petróleo, gas y los cereales que haya).
   Desplázate unos meses hacia atrás con la rueda del ratón para que MT5 descargue el historial.
2. Arrastra el script `Comprobar_Cuenta_y_Costes_6_Ventajas` a cualquier gráfico. En los parámetros pon el **nombre exacto** de cada símbolo
   (míralo en la Observación de mercado; en algunas cuentas llevan sufijo) y en `InpCestaE12` las materias primas que existan.
3. Mándame: la pestaña **Expertos** (clic derecho → Copiar) y el archivo `MQL5/Files/costes_6_ventajas.csv`.
   - Con esto te digo qué ventajas compensan en tu cuenta (OK / JUSTO / CARO) y qué Sharpe esperar (≈ 1,3 o ≈ 1,9).

## Fase 2 — Backtest en el Probador de MT5 (1-2 horas de ordenador)
Sirve para comprobar que el EA **opera a las horas y con los tamaños correctos** con los precios de tu bróker. No sirve para "optimizar": no se cambian parámetros.
1. *Ver → Probador de estrategias* (Ctrl+R).
2. Ajustes:
   - Experto: `Cartera_6_Ventajas_EA`. Símbolo del gráfico: `EURUSD`. Periodo: M1.
   - Modelo: **"Cada tick basado en ticks reales"** (o "OHLC de 1 minuto" si va lento).
   - Fechas: **2025.01.01 → hoy** (los festivos de EE. UU. del EA empiezan en 2025; antes de 2025 no detectaría las vísperas de festivo).
   - Depósito 100.000 USD y el apalancamiento de tu cuenta.
   - Parámetros: `InpOffsetServidorInv = 2` (FTMO y MetaQuotes), modo FONDEADO, el resto por defecto.
3. Al terminar, mándame: el **informe** (pestaña *Backtest*, clic derecho → Informe → guardar) y el archivo de registro del EA. Este último está en la carpeta del
   agente del probador: `MQL5/Tester/Agent-.../MQL5/Files/Cartera_6_Ventajas_log.csv`.
4. Qué compruebo yo:
   - que cada estrategia entra y sale a su hora y en sus días;
   - que el número de operaciones por estrategia es el esperado (euro ~250/año, oro ~50, yen de fin de mes 12, plata y materias primas ~9, yen de fin de trimestre 4);
   - que los tamaños y los stops tienen sentido y no hay errores de margen.
   Aviso: el filtro de noticias no funciona en el Probador (el calendario de MT5 no está disponible ahí) y ~2 años son pocos para juzgar el Sharpe.

## Fase 3 — Demo en tiempo real (mínimo 2-3 meses)
1. Pon el EA en **un solo gráfico** de la demo, con *Algo Trading* activado, en **modo FONDEADO**.
2. Rellena `InpFechasBCE` con las fechas de reunión del BCE (ecb.europa.eu → política monetaria → calendario), formato `2026.10.29,2026.12.17`.
3. **El terminal tiene que estar encendido** a las horas de operación (lista abajo; la del yen de fin de trimestre es de madrugada). Opciones: dejar el PC encendido
   o usar un VPS (por ejemplo el de MetaQuotes desde el propio MT5; tiene coste mensual: decisión tuya).
4. **Primera semana:** comprueba en la pestaña *Historial* que las operaciones salen a las horas de la tabla y mándame la pestaña *Expertos*
   si ves algo raro (errores, "simbolo_no_encontrado", "sin_entrada_sigma"…).
5. **Cada 2-4 semanas** mándame `MQL5/Files/Cartera_6_Ventajas_log.csv`. Comparo spreads, deslizamientos y resultados con el backtest.

### Horas de operación en España (horario normal; en las ~3 semanas al año de desfase horario, marzo y finales de octubre, una hora antes)
| Estrategia | Días | Hora de España |
|---|---|---|
| Euro | laborables | 12:00 → 14:00 |
| Yen fin de mes | antepenúltimo día laborable del mes | 13:00 → 14:00 |
| Yen fin de trimestre | último día laborable de mar/jun/sep/dic | 06:30 → 08:00 |
| Materias primas | día antes de víspera de festivo de EE. UU. → víspera | 19:55 → 19:55 del día siguiente |
| Oro | viernes | 22:00 → 22:55 |
| Plata | víspera de festivo de EE. UU. | 22:00 → 22:55 |

## Fase 4 — Decidir
Tras 2-3 meses de demo, lo que se juzga es **la ejecución**, no la ganancia (en 3 meses el resultado depende mucho de la suerte):
- ¿Opera a sus horas sin errores?
- ¿Los spreads y deslizamientos reales están cerca de lo medido en la fase 1?
- ¿El resultado está dentro de lo razonable? Con Sharpe ≈ 1,3, un trimestre negativo es normal (~30 % de probabilidad).
Si todo cuadra, el siguiente paso sería un examen de fondeo en **modo EXAMEN**. Comprarlo es decisión tuya; yo no compro ni abro cuentas.
