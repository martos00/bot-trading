# H74 — Noise Area SPY (Zarattini-Aziz-Barbon): resultados de la reproducción (2008-01 → 2021-05)

**Estado: reproducción fiel validada dentro de muestra. Fuera de muestra pendiente de datos con volumen.**

- Datos: SPY 1 minuto con volumen (Kaggle `rockinbrock/spy-1-minute-data`, formato Interactive Brokers).
  305.438 marcas duplicadas, todas idénticas, eliminadas. Hora en Mountain Time verificada contra los
  cierres de Yahoo (mediana |dif| = 1,2 pb). 27 días de media sesión excluidos. Auditoría de calidad:
  un hueco GRAVE (20-26 dic 2013; falta el 23-dic).
- **Fidelidad: correlación de las rentabilidades mensuales con la tabla publicada = 0,965** (158 meses).
  Media mensual 1,25% frente a 1,48% del paper (comisión escalonada no modelada).
- Dos motores independientes (numpy vectorizado y Python puro minuto a minuto): idénticos (1e-16).

| Coste por acción y lado (SPY) | Equivale a | IRR | Sharpe | MDD |
|---|---|---|---|---|
| 0 $ | sin costes | 18,3% | 1,23 | 26,6% |
| 0,0045 $ | costes del paper (IB + deslizamiento) | 14,8% | 1,03 | 30,3% |
| 0,01 $ | | 10,8% | 0,77 | 34,7% |
| 0,0175 $ | ≈ futuros ES/MES con 1 tick + comisión | 5,4% | 0,43 | 40,8% |
| **0,025 $** | **≈ CFD US500 con 0,5 pt de spread** | **0,3%** | **0,09** | **61,1%** |
| 0,035 $ | | −6,1% | −0,35 | 80,2% |

Por años (coste del paper): 2008 +55%, 2009 +17%, 2010 −1%, 2011 +23%, 2012 +20%, 2013 +11%,
2014 +7%, 2015 +18%, 2016 −17%, 2017 −9%, 2018 +41%, 2019 +8%, 2020 +22%, 2021 (hasta mayo) +18%.

**Fondeo (dentro de muestra, `h74_fondeo_insample.txt`):** con costes de CFD la probabilidad de superar
FTMO 2-Step es del 24-38%, igual o peor que operar sin ventaja. Con costes de futuros, 49-77%, pero
a los tamaños que sobreviven se tardan cientos de días hábiles. **Conclusión provisional: no apta
para fondeo con CFD; con futuros merece la validación fuera de muestra (jun-2021 → oct-2026).**
