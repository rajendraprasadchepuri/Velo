import pandas as pd
import yfinance as yf
import os
from datetime import datetime
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CSV_PATH = os.path.join(DATA_DIR, "live_trades.csv")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class TradeTracker:
    def __init__(self):
        self.filepath = CSV_PATH
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            df = pd.DataFrame(columns=[
                "TradeID", "Ticker", "SignalDate", "EntryPrice", "StopLoss", "TargetPrice",
                "Status", "ExitPrice", "ExitDate", "PnL", "Notes", "Strategy"
            ])
            df.to_csv(self.filepath, index=False)
        else:
            # Migration: Ensure Strategy column exists
            df = pd.read_csv(self.filepath)
            if "Strategy" not in df.columns:
                df["Strategy"] = "MTF" # Default for existing records
                df.to_csv(self.filepath, index=False)

    def load_trades(self):
        self._ensure_file_exists()
        return pd.read_csv(self.filepath)

    def save_trades(self, df):
        df.to_csv(self.filepath, index=False)

    def add_trade(self, signal_data, strategy_type="MTF"):
        df = self.load_trades()
        
        # Check if trade already exists for this ticker on this date to prevent duplicates
        date_str = datetime.now().strftime("%Y-%m-%d")
        ticker = signal_data.get('Ticker')
        
        # Avoid duplicate entries for same day and strategy
        existing = df[(df['Ticker'] == ticker) & (df['SignalDate'] == date_str) & (df['Strategy'] == strategy_type)]
        if not existing.empty:
            return False, "Trade already exists for today."

        # Parse Entry Price
        entry_price = float(signal_data.get('Entry Price', signal_data.get('Current Price', signal_data.get('Safe Entry', 0))))
        
        # Parse Stop Loss & Target
        sl = signal_data.get('Stop Loss')
        if sl is None:
             # Fallback for Intraday if not present
             sl = entry_price * 0.995 # 0.5% SL default
             
        target = signal_data.get('Target Price')
        if target is None:
            # Intraday 'Exit Price'
            target = signal_data.get('Exit Price', entry_price * 1.005)

        # Initial Status
        # MTF: OPEN (Market/Limit assumed filled for now, or could be WAITING_ENTRY but logic is simpler)
        # Intraday: WAITING_ENTRY (Strict requirement to hit price after 09:20)
        initial_status = "WAITING_ENTRY" if strategy_type == "Intraday" else "OPEN"

        new_trade = {
            "TradeID": str(uuid.uuid4())[:8],
            "Ticker": ticker,
            "SignalDate": date_str,
            "EntryPrice": entry_price,
            "StopLoss": float(sl),
            "TargetPrice": float(target),
            "Status": initial_status, 
            "ExitPrice": None,
            "ExitDate": None,
            "PnL": 0.0,
            "Notes": signal_data.get('Signal', 'Manual'),
            "Strategy": strategy_type
        }
        
        df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
        self.save_trades(df)
        return True, "Trade added successfully."

    def update_status(self):
        df = self.load_trades()
        updates_count = 0
        from datetime import time
        
        for index, row in df.iterrows():
            status = row['Status']
            if status in ['TARGET_HIT', 'STOP_LOSS_HIT', 'NOT_TRIGGERED', 'EXIT_AT_CLOSE']:
                continue
                
            ticker = row['Ticker']
            start_date = row['SignalDate']
            strategy = row.get('Strategy', 'MTF')
            
            try:
                # --- STRATEGY SPECIFIC LOGIC ---
                
                if strategy == 'Intraday':
                    # Intraday Logic: 5m candles, same day only
                    # Fetch data. Note: yfinance limits 5m data effectively (last 60 days).
                    # We need to fetch data covering the SignalDate.
                    # start=SignalDate, end=SignalDate + 1 day
                    start_dt = pd.to_datetime(start_date)
                    end_dt = start_dt + pd.Timedelta(days=1)
                    
                    data = yf.download(ticker, start=start_dt, end=end_dt, interval="5m", progress=False, auto_adjust=True)
                    
                    if data.empty: continue
                    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

                    # Filter for specific day just in case
                    # (Strictly speaking yf download with start/end handles dates, but we check times)
                    
                    target = row['TargetPrice']
                    sl = row['StopLoss']
                    entry = row['EntryPrice']
                    
                    status_changed = False
                    
                    for timestamp, candle in data.iterrows():
                        # Skip first 5 mins (09:15 - 09:20)
                        # Candle timestamp is usually open time. 09:15 candle covers 09:15-09:20.
                        # So we process candles starting from 09:20 onwards? 
                        # User said "skipping 5mins bulling candle". If we assume market opens 9:15,
                        # we ignore anything happening in 09:15 candle.
                        if timestamp.time() < time(9, 20):
                            continue
                            
                        # Stop at market close 15:30
                        if timestamp.time() >= time(15, 30):
                            break

                        high = candle['High']
                        low = candle['Low']
                        
                        # STATE MACHINE
                        if row['Status'] == 'WAITING_ENTRY':
                            # Trigger if price touches Entry
                            # Conservative: strictly Low <= Entry <= High
                            if low <= entry <= high:
                                row['Status'] = 'OPEN'
                                row['Notes'] = f"{row.get('Notes', '')} | Triggered at {timestamp.time()}"
                                # If triggered, we must ALSO check if it hit SL/Target in same candle?
                                # Ideally yes. Conservative: Check SL first.
                                # But if just entered, maybe give it space? 
                                # Let's check immediately to be safe/accurate to volatility.
                                status_changed = True
                                # Fallthrough to OPEN logic immediately

                        if row['Status'] == 'OPEN':
                            # Priority: SL Safety first.
                            if low <= sl:
                                row['Status'] = "STOP_LOSS_HIT"
                                row['ExitPrice'] = sl
                                row['ExitDate'] = timestamp.strftime("%Y-%m-%d")
                                row['PnL'] = (sl - entry) / entry * 100
                                row['Notes'] = f"{row.get('Notes', '')} | SL Hit at {low}"
                                status_changed = True
                                break # Trade complete

                            if high >= target:
                                row['Status'] = "TARGET_HIT"
                                row['ExitPrice'] = target
                                row['ExitDate'] = timestamp.strftime("%Y-%m-%d")
                                row['PnL'] = (target - entry) / entry * 100
                                row['Notes'] = f"{row.get('Notes', '')} | Target Hit at {high}"
                                status_changed = True
                                break # Trade complete
                    
                    # End of Day Processing
                    # If we processed all data and day is over (current time > 15:30 on signal day)
                    # We need to know if "Day is Done". 
                    # If SignalDate < Today -> Day is definitely done.
                    # If SignalDate == Today -> Only done if now > 15:30.
                    
                    is_day_done = False
                    now = datetime.now()
                    signal_dt_obj = datetime.strptime(start_date, "%Y-%m-%d")
                    if signal_dt_obj.date() < now.date() or (signal_dt_obj.date() == now.date() and now.time() > time(15, 30)):
                        is_day_done = True
                    
                    if is_day_done and not status_changed: # Only if we haven't just finished it above
                        if row['Status'] == 'WAITING_ENTRY':
                            row['Status'] = 'NOT_TRIGGERED'
                            row['Notes'] = f"{row.get('Notes', '')} | Expired (No Entry)"
                            status_changed = True
                        elif row['Status'] == 'OPEN':
                            # Square off at close price of last candle
                            last_close = data.iloc[-1]['Close']
                            row['Status'] = 'EXIT_AT_CLOSE'
                            row['ExitPrice'] = last_close
                            row['ExitDate'] = start_date
                            row['PnL'] = (last_close - entry) / entry * 100
                            row['Notes'] = f"{row.get('Notes', '')} | Auto-Squareoff"
                            status_changed = True

                    if status_changed:
                        df.loc[index] = row
                        updates_count += 1

                else:
                    # --- MTF / SWING LOGIC (Existing) ---
                    data = yf.download(ticker, start=start_date, progress=False, auto_adjust=True)
                    if data.empty: continue
                    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
                    
                    target = row['TargetPrice']
                    sl = row['StopLoss']
                    entry = row['EntryPrice']
                    status_changed = False
                    
                    for date, day_data in data.iterrows():
                        current_date_str = date.strftime("%Y-%m-%d")
                        
                        # Swing: Skip Signal Date to avoid look-ahead bias
                        if current_date_str == start_date:
                            continue
                            
                        high = day_data['High']
                        low = day_data['Low']
                        
                        if low <= sl:
                            row['Status'] = "STOP_LOSS_HIT"
                            row['ExitPrice'] = sl
                            row['ExitDate'] = current_date_str
                            row['PnL'] = (sl - entry) / entry * 100
                            row['Notes'] = f"{row.get('Notes', '')} | SL Hit at {low}"
                            status_changed = True
                            break 
                            
                        if high >= target:
                            row['Status'] = "TARGET_HIT"
                            row['ExitPrice'] = target
                            row['ExitDate'] = current_date_str
                            row['PnL'] = (target - entry) / entry * 100
                            row['Notes'] = f"{row.get('Notes', '')} | Target Hit at {high}"
                            status_changed = True
                            break 
                    
                    if status_changed:
                        df.loc[index] = row
                        updates_count += 1
            
            except Exception as e:
                print(f"Error updating {ticker}: {e}")
                
        if updates_count > 0:
            self.save_trades(df)
            
        return updates_count
