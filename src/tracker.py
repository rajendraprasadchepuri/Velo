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
        # MTF strategy has 'Entry Price' or 'Current Price'
        # Intraday might have 'Safe Entry'
        entry_price = float(signal_data.get('Entry Price', signal_data.get('Current Price', signal_data.get('Safe Entry', 0))))
        
        # Parse Stop Loss & Target
        # MTF has 'Stop Loss', 'Target Price'
        # Intraday needs calculation if not provided
        sl = signal_data.get('Stop Loss')
        if sl is None:
             # Fallback for Intraday if not present
             sl = entry_price * 0.995 # 0.5% SL default
             
        target = signal_data.get('Target Price')
        if target is None:
            # Intraday 'Exit Price'
            target = signal_data.get('Exit Price', entry_price * 1.005)

        new_trade = {
            "TradeID": str(uuid.uuid4())[:8],
            "Ticker": ticker,
            "SignalDate": date_str,
            "EntryPrice": entry_price,
            "StopLoss": float(sl),
            "TargetPrice": float(target),
            "Status": "OPEN", 
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
        
        for index, row in df.iterrows():
            if row['Status'] != 'OPEN':
                continue
                
            ticker = row['Ticker']
            start_date = row['SignalDate']
            
            # Fetch data from signal date to today
            # yfinance download expects start date. 
            try:
                # auto_adjust=True accounts for splits/dividends which is important for PnL
                data = yf.download(ticker, start=start_date, progress=False, auto_adjust=True)
                
                if data.empty:
                    continue
                
                # Handling MultiIndex
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                
                # Check each day since signal
                # If signal was today, we might only have today's data or none if market closed/pre-open
                
                target = row['TargetPrice']
                sl = row['StopLoss']
                entry = row['EntryPrice']
                
                status_changed = False
                exit_price = 0
                exit_date = ""
                
                for date, day_data in data.iterrows():
                    # Skip the signal date itself if we assume entry happens *at* signal price 
                    # but typically we track subsequent movement.
                    # For simplicity, let's check High/Low of ALL available data including signal day
                    # (Conservative: If SL hit on day 1, it's a loss. If Target hit, it's a win.)
                    
                    high = day_data['High']
                    low = day_data['Low']
                    
                    # Logic: Did we hit SL? Did we hit Target?
                    # Priority: If High > Target, we win. If Low < SL, we lose.
                    # Conflict: What if both in same candle? 
                    # Conservative approach: Assume SL hit first if close to open, or check Open vs ... 
                    # Simplest: If Low <= SL -> Hit SL. Else if High >= Target -> Hit Target.
                    
                    if low <= sl:
                        row['Status'] = "STOP_LOSS_HIT"
                        row['ExitPrice'] = sl
                        row['ExitDate'] = date.strftime("%Y-%m-%d")
                        row['PnL'] = (sl - entry) / entry * 100
                        status_changed = True
                        break # Trade closed
                        
                    if high >= target:
                        row['Status'] = "TARGET_HIT"
                        row['ExitPrice'] = target
                        row['ExitDate'] = date.strftime("%Y-%m-%d")
                        row['PnL'] = (target - entry) / entry * 100
                        status_changed = True
                        break # Trade closed
                
                if status_changed:
                    df.loc[index] = row
                    updates_count += 1
                    
            except Exception as e:
                print(f"Error updating {ticker}: {e}")
                
        if updates_count > 0:
            self.save_trades(df)
            
        return updates_count
