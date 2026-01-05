# Velo Trading System

Velo is a professional-grade trading analysis and tracking system built for the Indian Stock Market (NSE). It combines technical analysis, automated scanning, and live trade tracking for both Swing (MTF) and Intraday strategies.

## 🚀 Key Features

### 1. Live Trade Tracker

* **Real-time Monitoring**: Tracks your open trades against live market data.
* **Precision Timing**: Uses **1-minute candles** for Intraday trades to ensure exact Entry, Hit, and Miss detection.
* **Dynamic Management**:
  * **Trailing Stoploss**: Automatically moves Stoploss to Break-Even/Profit when Targets are hit.
  * **Target Extension**: Automatically extends Target Price by 0.5% upon reaching goals to ride trends.
* **Smart Status**: Detects `TARGET_HIT`, `STOP_LOSS_HIT`, `WAITING_ENTRY`, and `EXIT_AT_CLOSE`.
* **Persistence**: Automatically saves all trade history to `data/live_trades.csv`.
* **Performance Dashboard**: View PnL, Win Rate, and detailed logs in the "Live Performance" page with precise IST timestamps.

### 2. Intraday Strategy (High Octane)

* **High-Beta Watchlist**: Scans ~75 high-momentum stocks (Banks, Auto, Adani, Defense) for maximum daily range.
* **Logic**: Uses EMA, VWAP, RSI, VSA (Volume Spread Analysis), and Sector Momentum to score setups.
* **Smart Planning**:
  * **Pre-Market**: Runs specifically for "Today".
  * **Post-Market**: Auto-defaults to "Tomorrow" for planning ahead.
  * **Granular Tracking**: Uses 1-minute data to validate entries (Must strictly cross entry price).
  * **Auto-Expiry**: Trades not triggered by 3:30 PM are marked `NOT_TRIGGERED`. Open trades are squared off as `EXIT_AT_CLOSE` at 15:30:00.

### 3. MTF / Swing Strategy

* **Daily Timeframe**: Analyzes daily candles for multi-day trends.
* **Quality Watchlist**: Focuses on Nifty 50 and key Sector Leaders for stability.
* **Safety First**: Prioritizes Stop Loss safety in volatile conditions.

### 4. Automation 🤖

* **One-Click Scan**: Double-click `run_intraday_scan.bat` to run the Intraday analysis instantly.
* **Task Scheduler Ready**: Can be scheduled to run automatically at 9:45 AM daily.
* **Auto-Add**: Automatically adds high-confidence (>90 Score) trades to your tracker.

---

## 📂 Project Structure

* `Hello.py`: Main Streamlit Dashboard.
* `pages/`:
  * `Intraday.py`: Manual Intraday Scanner UI.
  * `MTF_Strategy.py`: Swing Trading Scanner UI.
  * `Live_Performance.py`: Dashboard for tracking active trades.
* `src/`:
  * `tracker.py`: Core trade tracking engine (Handles 1m data fetching, logic state machine).
  * `intraday_strategy.py`: Shared logic and watchlist for Intraday.
  * `mtf_strategy.py`: Logic for Swing trading.
* `tests/`: Contains verification scripts for testing logic integrity.
* `auto_run_intraday.py`: Python script for automated scanning.
* `run_intraday_scan.bat`: Batch file for easy execution.

---

## 🛠️ How to Use

### Manual Workflow

1. Run the app: `streamlit run Hello.py`
2. Go to **Intraday** or **MTF Strategy** page.
3. Click "Calculate Scores".
4. Review the table. High confidence trades are highlighted.
5. Click **"Add to Live Tracker"**.
6. Monitor progress in **Live Performance** page.

### Automated Workflow (Intraday)

1. **Schedule**: Set Windows Task Scheduler to run `run_intraday_scan.bat` at **09:45 AM**.
2. **Forget**: The system will scan, filter, and add trades to your tracker automatically.
3. **Review**: Check the "Live Performance" page to see your active/pending trades.

---

## ⚙️ Configuration

* **Watchlists**: Defined in `src/intraday_strategy.py` (Intraday) and `src/mtf_strategy.py` (Swing).
* **Data**: All trade data is stored in `data/live_trades.csv`. You can back this up manually if needed.
