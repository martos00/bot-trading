# Reglas de prop firms relevantes para un bot (consultado el 19-oct-2026)

Las reglas cambian a menudo. Cada dato lleva su **nivel de confianza**:
**[O]** página oficial leída directamente · **[O*]** página oficial vista a través de un resumen de buscador ·
**[3]** solo fuentes de terceros (blogs, comparadores, afiliados; pueden estar desactualizadas o contradecirse).
Antes de comprar cualquier evaluación hay que releer los términos oficiales vigentes.

## CFD / Forex

### FTMO — https://ftmo.com/en/trading-objectives/ (modificada 12-oct-2026) [O]
| Regla | 2-Step | 1-Step | Notas |
|---|---|---|---|
| Objetivo | 10% (Challenge) + 5% (Verification) | 10% | Sin objetivo en la cuenta financiada |
| Pérdida diaria | 5% del capital inicial | 3% | Se recalcula a las 00:00 CE(S)T: saldo a esa hora − límite. Se compara con la **equity** (incluye flotante, swaps y comisiones) |
| Pérdida máxima | 10% **estática** (desde el capital inicial) | 10% **trailing de cierre de día** (máximo saldo a 00:00, solo sube) | Instant: 10% trailing intradía |
| Días mínimos | 4 por fase | — | Día de trading = día con al menos una posición abierta |
| Consistencia | Cuentas desde el 12-oct-2026: el mejor día ≤ 50% del beneficio total | 1-Step: regla "Best Day" | Superarla no es incumplimiento: obliga a seguir operando hasta cumplir el ratio |
- EAs: permitidos según varias fuentes, prohibidos HFT y arbitraje, sin aprobación previa **[3]**.
- Noticias: en la cuenta financiada estándar no se puede abrir ni cerrar en ±2 min de noticias de alto impacto en el instrumento afectado; la cuenta Swing está exenta **[3, fuentes contradictorias]**.
- Fin de semana: permitido en evaluación; en la cuenta financiada estándar hay que cerrar; Swing lo permite con apalancamiento menor **[3]**.

### FundedNext Stellar 2-Step — help.fundednext.com [O*]
- Objetivos 8% (fase 1) y 5% (fase 2); pérdida diaria 5% del saldo inicial (cuenta el flotante); pérdida máxima 10% **estática**; 5 días mínimos por fase.
- Noticias: las operaciones abiertas en ±5 min de noticias de alto impacto en un par correlacionado solo computan el 40% del beneficio (no es prohibición).
- EAs permitidos; prohibidas estrategias "explotadoras" y el copy trading no autorizado; usar una sola IP o VPS fija.

### The5ers — the5ers.com [O, parcial]
- Una tabla de la portada muestra pérdida máxima 6%, pérdida diaria 3%, objetivo 10%, consistencia 50% por día y apalancamiento 1:100. La asignación de columnas a cada programa es ambigua y no se indica si la pérdida es estática o trailing. **Pendiente de leer los términos completos.**

### FundingPips, E8 y otras
- No consultadas todavía.

## Futuros

### Topstep — help.topstep.com [O para el MLL; [3] para el resto]
- **Maximum Loss Limit [O]:** $2.000 / $3.000 / $4.500 (cuentas de 50K / 100K / 150K). Sube con el saldo de cierre de día, no baja nunca y queda fijo al alcanzar el saldo inicial. Las pérdidas no realizadas que lo toquen liquidan la cuenta de inmediato.
- Objetivo $3.000 / $6.000 / $9.000; consistencia: el mejor día ≤ 50-55% del beneficio (fuentes discrepantes; incumplirla sube el objetivo); límite diario opcional en el Combine y obligatorio en la cuenta Live **[3]**.
- Automatización: se permite vía la API de TopstepX según varias fuentes; prohibidos HFT y explotación del simulador; una fuente dice que no se permite VPS/VPN **[3, sin confirmar]**.

### Apex Trader Funding [3, web oficial con acceso bloqueado (403)]
- Trailing drawdown de cierre de día o intradía según el tipo de cuenta; deja de seguir el máximo al llegar al saldo inicial + 100 $ (en Tradovate podría no detenerse).
- **Automatización: varias fuentes indican que el trading totalmente automatizado está prohibido en las cuentas financiadas (PA).** Si se confirma, **Apex es incompatible con el objetivo de un bot autónomo.**

## Implicaciones para el diseño del bot

1. **Pérdida máxima estática frente a trailing.** La estática (FTMO 2-Step, FundedNext) es mucho más favorable para estrategias con varianza. La trailing intradía (Apex intradía, FTMO Instant) penaliza las estrategias que dejan correr beneficios no realizados.
2. **La pérdida diaria se mide con la equity flotante.** El bot tiene que vigilar el flotante en tiempo real, no solo las operaciones cerradas. Un stop no garantiza el límite: hay gaps, slippage y spreads en noticias.
3. **Las reglas de consistencia** (mejor día ≤ 30-55% del beneficio) penalizan las estrategias de cola derecha con pocos días muy grandes. Hay que medir la distribución del P&L diario, no solo su media.
4. **Intradía sin posiciones overnight** evita swaps, gaps de fin de semana y restricciones de la cuenta estándar.
5. **Los EAs están permitidos en FTMO y FundedNext;** en futuros hay que verificar caso a caso. Quedan excluidos HFT, arbitraje de latencia y explotación del simulador.
