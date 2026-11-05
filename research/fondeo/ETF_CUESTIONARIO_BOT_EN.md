# Answer to Elite Trader Funding's Risk team questionnaire (draft, 05-Nov-2026) — to be sent by the user

Hello Alex,

Thank you for the detailed answers. Here is the information requested for the Risk team review.

**1. Strategy Summary**
- What it does: a rules-based, schedule-driven futures strategy. It trades a small set of recurring, time-specific patterns that we
  researched and tested on 2010-2026 data, for example: long Micro Gold on Fridays from 4:00 to 4:55 PM ET; long Silver on Fridays
  from 4:30 to 4:57 PM ET and on the day before US market holidays; Japanese yen around month-end and quarter-end (fixed one-hour
  windows); Nikkei on specific quarter days; and, on some days, a break of the Asian-session range in gold/copper/Nikkei with a
  fixed stop and target. Every entry has a predefined exit time; positions are always flat by 4:57 PM ET on 1-Step accounts.
- Fully automated: yes. It runs as a NinjaTrader 8 strategy (NinjaScript), placing and managing its own orders. I supervise it every day.

**2. Execution**
- Assets: Micro Gold (MGC), Silver (SIL or SI), Japanese yen (MJY or 6J), Micro Copper (MHG), Nikkei 225 (NKD) — only those on your
  supported list.
- Frequency: on a 150K account about 360 trades per year on about 230 days (typically 1-4 orders per day); on smaller accounts about
  130 trades per year. Holding times from 30 minutes to several hours. It is not high-frequency and does not scalp.
- Order types: market orders for entries and exits, plus one protective stop-market order per open position resting on the server.

**3. Risk Controls**
- Position size from a fixed risk per trade (a fraction of a percent of the account) based on recent volatility; hard cap on total open
  contracts (configurable; e.g. 3 for DTF accounts) and on exposure per trade.
- Every position has a stop: a catastrophe stop (4 standard deviations) or the strategy's own stop, plus a protective stop-market order
  on the server.
- Daily loss limit inside the strategy (flattens everything and stops trading for the day), time-based exits, and no entry if the
  session closes before the planned exit.
- It never adds to losing positions, never uses martingale, and never hedges between accounts.

**4. Monitoring**
- I monitor it daily on the NinjaTrader platform.
- Logs: every signal, entry, exit, reason for not trading, fill price, slippage and commission is written to a CSV log, plus a daily
  P&L file. I review them weekly.
- Developed by: me, Miguel, with the help of an AI coding assistant. It is not purchased, rented, shared or copied from any
  third-party source, and no one else uses it.

**5. Fail-safes**
- Disconnections: each open position has a protective stop-market order resting on the broker's server, so it stays protected if my
  computer or connection fails. After reconnecting, the strategy keeps its state and immediately closes any position whose exit time
  has passed.
- Errors: on an order error the strategy stops, cancels working orders and closes positions (NinjaTrader "stop, cancel and close").
- It runs on a dedicated computer that is kept on during trading hours.
- I understand that I am responsible for the strategy at all times.

**Questions**
1. Could you confirm that MGC, SIL, MJY (or 6J), MHG and NKD are on the supported list for 1-Step and DTF accounts?
2. Once approved, may the same strategy run on all my accounts (up to 15 1-Step + 5 DTF)?
3. What are the payout limits per reward cycle for the 150K 1-Step and the 100K DTF?

Thank you very much.

Best regards,
Miguel
