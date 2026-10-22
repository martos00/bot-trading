# Cartera de 6 ventajas — instrucciones para la demo

## Archivos
- `Scripts/Comprobar_Cuenta_y_Costes_6_Ventajas.mq5`: comprueba la cuenta y mide el coste real de cada ventaja. **No opera.**
- `Experts/Cartera_6_Ventajas_EA.mq5`: el EA que opera las 6 ventajas (por defecto solo en cuentas **demo**).

## Paso 1 — Medir costes (una vez)
1. Copia el script a `MQL5/Scripts` de tu MT5 y compílalo en MetaEditor (F7). Si sale algún error, mándamelo.
2. Abre un gráfico **M1** de cada símbolo (EURUSD, USDJPY, EURJPY, GBPJPY, XAUUSD, XAGUSD, petróleo, gas, cereales…) y desplázate unos meses hacia atrás
   para que MT5 descargue el historial.
3. Arrastra el script a cualquier gráfico. En los parámetros escribe el **nombre exacto** de cada símbolo en tu cuenta (en FTMO pueden llevar sufijo)
   y, en `InpCestaE12`, las materias primas que existan (por ejemplo `USOIL,UKOIL,NATGAS,CORN,SOYBEAN,WHEAT`).
4. Mándame el diario "Expertos" y el fichero `MQL5/Files/costes_6_ventajas.csv`.
   - El script indica para cada ventaja si el coste es **OK** (≤ 1/3 de la ventaja), **JUSTO** o **CARO**.
   - También dice el **apalancamiento efectivo** de cada símbolo (el oro necesita de media unas 5 veces el capital).

## Paso 2 — EA en demo
1. Copia el EA a `MQL5/Experts`, compílalo y ponlo en **un solo gráfico** (cualquiera). Activa "Algo Trading".
2. Parámetros importantes:
   - `InpModo`: **FONDEADO** (riesgo normal) o **EXAMEN** (riesgo × `InpMultExamen`, por defecto ×2).
   - `InpRiesgoPct` = 0,5 % por operación (riesgo = volatilidad objetivo).
   - `InpPerdidaDiariaMaxPct` = 3,5 % (por debajo del 5 % de FTMO) y `InpPerdidaTotalMaxPct` = 8 % (por debajo del 10 %).
   - Nombres de los símbolos (igual que en el script) y `InpCestaE12`.
   - `InpFechasBCE`: fechas de reunión de política monetaria del BCE, formato `AAAA.MM.DD,AAAA.MM.DD` (de ecb.europa.eu). Si se deja vacío,
     la ventaja del euro no se salta esos días (avisa al arrancar).
   - `InpFestivosNYSE`: viene con 2025-2027; ampliar cuando haga falta.
   - `InpDSTServidor`: FTMO y MetaQuotes-Demo usan el horario de verano **europeo** (valor por defecto).
3. Cada estrategia se puede activar o desactivar por separado.
4. El EA guarda cada evento (entradas, salidas, stops, días sin operar y motivo) en `MQL5/Files/Cartera_6_Ventajas_log.csv`.
   Mándamelo cada 2-4 semanas para comparar con el backtest.

## Qué hace cada estrategia (hora de Nueva York)
| Estrategia | Símbolo(s) | Días | Entrada → salida |
|---|---|---|---|
| E2 euro | EURUSD corto | laborables salvo festivos TARGET / Inglaterra / BCE | 06:00 → 08:00 |
| E8 oro | XAUUSD largo | viernes (no festivos) | 16:00 → 16:55 |
| E10 plata | XAGUSD largo | víspera de festivo NYSE | 16:00 → 16:55 |
| E9 yen fin de mes | USDJPY largo | antepenúltimo día laborable del mes | 07:00 → 08:00 |
| E11 yen fin de trimestre | USDJPY, EURJPY, GBPJPY corto (1/3 c/u) | último día laborable de mar/jun/sep/dic | 00:30 → 02:00 |
| E12 materias primas | cesta larga (igual riesgo) | día antes de la víspera de festivo | 13:55 → 13:55 del día siguiente |

## Protecciones
- No abre ni cierra a ±2 minutos de una noticia de **alto impacto** de las divisas implicadas (calendario de MT5): si la hay al entrar, ese día no opera;
  si la hay al salir, espera hasta 5 minutos.
- Pérdida diaria: si el día pierde `InpPerdidaDiariaMaxPct`, cierra todo y no opera más ese día.
- Pérdida total: si se pierde `InpPerdidaTotalMaxPct` desde el balance inicial, deja de operar.
- Stop de catástrofe en cada operación a 4 desviaciones de la franja.
- `InpSoloDemo = true`: no opera en cuentas reales.
- E12 nunca mantiene posiciones durante el fin de semana (si la víspera es lunes, ese festivo no se opera).

## Diferencias conocidas con el backtest
- Tamaño: E9, E10, E11 y E12 estiman la volatilidad con la misma franja de los últimos 60 días laborables (no solo los días de la señal, que son pocos);
  E8 usa los últimos 52 viernes y E2 los últimos 60 días, como en el backtest.
- E12 entra y sale a las 13:55 NY (los cereales cierran a las 14:20); el backtest usó cierres diarios.
- El EA no está compilado ni probado en este entorno (no hay MetaEditor): la primera compilación y unos días de demo sirven de prueba.
