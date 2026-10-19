# Datos de Alpaca (solo datos / paper trading) — instrucciones de configuración

**No escribas nunca las claves en el chat ni en el repositorio.** Se leen solo desde variables de entorno.

## Qué ofrece el plan gratuito (documentación oficial consultada el 19-oct-2026)
- docs.alpaca.markets/docs/about-market-data-api, plan **Basic (gratuito)**: histórico de acciones y ETF
  **desde 2016**, con la limitación de no servir los **últimos 15 minutos**; 200 llamadas/min.
- Tiempo real: solo el feed IEX. Pendiente de comprobar en la práctica si el histórico de 1 minuto con
  `feed=sip` (volumen consolidado) está disponible en el plan gratuito; una réplica pública (Brusco) solo
  usó IEX desde 2020-07. **El primer paso de la descarga verificará esto y lo registrará**.

## Pasos (los haces tú; no cuestan dinero)
1. Crear una cuenta en alpaca.markets y usar **solo la cuenta Paper** (no hace falta depositar ni operar).
2. En el panel Paper → "API Keys" → generar una clave. Guarda la *Key ID* y el *Secret*.
3. Añadirlas en la configuración del entorno de Claude Code (menú del entorno en la barra de título de la
   sesión → Edit → "Network secrets" / "API credentials" si aparece; si no, como variables de entorno):
   - `ALPACA_API_KEY_ID` = tu Key ID
   - `ALPACA_API_SECRET_KEY` = tu Secret
4. Abrir una sesión nueva en ese entorno. El script de descarga
   (`research/fondeo/descargar_alpaca.py`, se escribirá cuando haga falta) leerá solo esas variables, pedirá
   barras de 1 minuto con `feed=sip` y, si el plan no lo permite, informará del error en vez de usar IEX sin avisar.

Riesgo nulo: las claves de una cuenta Paper no pueden mover dinero real. Aun así, puedes revocarlas desde el panel en cualquier momento.
