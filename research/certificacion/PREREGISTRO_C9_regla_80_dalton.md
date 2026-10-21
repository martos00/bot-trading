# Pre-registro C9 — "Regla del 80%" del perfil de mercado (Dalton) en S&P 500 y Nasdaq 100 (21-oct-2026)

Redactado y enviado a git ANTES de calcular ningún resultado.

## Origen
TikTok de @tradingstraty ("Mean reversion trading", leída la transcripción): el mercado pasa la mayor parte del tiempo en
equilibrio; comprar o vender en los extremos del perfil de volumen apuntando al valor justo. El vídeo no da reglas. Se
prueba la regla concreta más conocida de esa escuela: la "regla del 80%" del Market Profile (J. Dalton, *Mind Over
Markets*): si el mercado abre fuera de la zona de valor del día anterior y vuelve a entrar en ella durante dos períodos
consecutivos de 30 minutos, tiende a recorrerla entera hasta el extremo opuesto. Ya probado y negativo en el proyecto:
reversión al VWAP, Bollinger, RSI(2), reversión asiática (G1). Expectativa previa: baja.

## Datos
HistData M1 (BID; hora de Nueva York con horario de verano, verificada en H69): SPXUSD (S&P 500, **principal**) y NSXUSD
(Nasdaq 100, informativo), 2010-01 → 2026-09. Sesión regular 09:30-16:00 NY, lunes a viernes; un día solo cuenta si tiene
≥ 350 minutos de datos en su sesión y la anterior.

## Reglas (sin parámetros que ajustar)
- **Perfil TPO del día anterior** (versión original, sin volumen): 13 períodos de 30 min (09:30, 10:00, …, 15:30). Precios
  en escalones del 0,05% del cierre anterior. Cada período suma 1 a cada escalón que tocó (entre su mínimo y su máximo).
  POC = escalón con más cuenta (si empatan, el más cercano al centro del rango). Zona de valor = desde el POC se añade el
  escalón vecino (arriba o abajo) con más cuenta hasta llegar al 70% del total; VAH/VAL = bordes superior/inferior.
- **Condición:** apertura de hoy (primer precio ≥ 09:30) por encima de VAH o por debajo de VAL.
- **Señal:** el primer par de períodos consecutivos de 30 min (desde 09:30) cuyos dos cierres están dentro de [VAL, VAH].
  Entrada al cierre del segundo período, como muy tarde a las 14:00 (si no, no hay operación).
- **Dirección y objetivo:** si abrió por encima → venta con objetivo VAL; si abrió por debajo → compra con objetivo VAH.
- **Stop:** el extremo del día hasta la entrada en el lado de la apertura (máximo del día para ventas, mínimo para compras).
- **Salida:** objetivo o stop (con velas M1; si ambos en la misma vela, se supone el stop), o al cierre de las 16:00.
  Una operación como máximo al día.

## Costes (CFD de índice de fondeo)
1,0 pb por ida y vuelta (spread 0,5 pb + deslizamiento 0,25 pb por lado). Estrés: 2,0 pb.

## Tramos y criterios (S&P 500)
- Descubrimiento 2010-2017: media neta por operación > 0 (comprobación de que la regla tuvo ventaja alguna vez).
- **Confirmación 2018 → 2026-09**, todos: (1) media neta > 0 con t ≥ 2,0; (2) media bruta ≥ 3 × coste;
  (3) neta positiva en ≥ 60% de los años.
- Informativo: % de operaciones que llegan al objetivo (la regla promete ≈ 80%), media en múltiplos de R, Nasdaq 100,
  estrés de costes. Contador +1 (N acumulado ≈ 1.160). Si falla, se descarta sin cambiar ningún detalle.
