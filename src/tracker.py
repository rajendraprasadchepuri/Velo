"""
tracker.py

Core engine for tracking and updating trade status.
Handles:
- Loading/Saving trades to CSV.
- Fetching live market data (Daily for MTF, 1-Minute for Intraday).
- State Machine logic for trade lifecycle (WAITING_ENTRY -> OPEN -> TARGET/SL HIT).
- Dynamic Stoploss and Target updates.
"""
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
                "Status", "ExitPrice", "ExitDate", "PnL", "Notes", "Strategy",
                "EntryDate", "UpdatedStopLoss"
            ])
            df.to_csv(self.filepath, index=False)
        else:
            # Migration: Ensure Strategy column and new columns exist
            df = pd.read_csv(self.filepath)
            changed = False
            if "Strategy" not in df.columns:
                df["Strategy"] = "MTF" # Default for existing records
                changed = True
            if "EntryDate" not in df.columns:
                df["EntryDate"] = None
                changed = True
            if "UpdatedStopLoss" not in df.columns:
                df["UpdatedStopLoss"] = None
                changed = True
                
                # --- NEW COLUMNS FOR ADVANCED STRATEGY ---
                if "ATR" not in df.columns: df["ATR"] = None
                if "TriggerHigh" not in df.columns: df["TriggerHigh"] = None
                if "VWAP" not in df.columns: df["VWAP"] = None
                if "InitialSL" not in df.columns: df["InitialSL"] = None
                if "Side" not in df.columns: df["Side"] = "BUY" # Default to BUY
                
            if changed:
                df.to_csv(self.filepath, index=False)

    def load_trades(self):
        self._ensure_file_exists()
        return pd.read_csv(self.filepath)

    def save_trades(self, df):
        df.to_csv(self.filepath, index=False)

    def add_trade(self, signal_data, strategy_type="MTF", signal_date=None):
        df = self.load_trades()
        
        if signal_date:
            date_str = signal_date
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        ticker = signal_data.get('Ticker')
        
        existing = df[(df['Ticker'] == ticker) & (df['SignalDate'] == date_str) & (df['Strategy'] == strategy_type)]
        
        # Parse common fields
        entry_price = float(signal_data.get('Entry Price', signal_data.get('Current Price', signal_data.get('Safe Entry', 0))))
        
        atr = signal_data.get('ATR')
        trigger_high = signal_data.get('TriggerHigh')
        vwap = signal_data.get('VWAP')
        
        # Calculate SL/Target based on ATR if available (RRR 1:2)
        side = signal_data.get('Side', 'BUY')
        
        from src.utils import round_to_tick
        
        # Calculate SL/Target based on ATR if available (RRR 1:2)
        if atr and float(atr) > 0:
            atr_val = float(atr)
            atr_risk = 1.5 * atr_val
            min_risk = entry_price * 0.005
            
            actual_risk = max(atr_risk, min_risk)
            
            if side == "SELL":
                # Short: SL above, Target below
                sl_price = entry_price + actual_risk
                target_price = entry_price - (2 * actual_risk)
            else:
                # Long: SL below, Target above
                sl_price = entry_price - actual_risk
                target_price = entry_price + (2 * actual_risk)
            
            sl = round_to_tick(sl_price)
            target = round_to_tick(target_price)
        else:
            # Fallback Defaults (0.5%)
            sl = signal_data.get('Stop Loss')
            target = signal_data.get('Target Price')
            
            if side == "SELL":
                 if sl is None: sl = entry_price * 1.005
                 if target is None: target = entry_price * 0.995
            else:
                 if sl is None: sl = entry_price * 0.995 
                 if target is None: target = entry_price * 1.005
                 
            sl = round_to_tick(sl)
            target = round_to_tick(target)

        initial_status = "WAITING_ENTRY" # Default for ALL strategies now (Intraday & MTF)

        if not existing.empty:
            existing_index = existing.index[0]
            if df.at[existing_index, 'Status'] == 'WAITING_ENTRY':
                 # Update existing
                 df.at[existing_index, 'EntryPrice'] = entry_price
                 df.at[existing_index, 'ATR'] = atr
                 df.at[existing_index, 'TriggerHigh'] = trigger_high
                 df.at[existing_index, 'VWAP'] = vwap
                 
                 # Update SL/Target with new logic
                 df.at[existing_index, 'StopLoss'] = float(sl)
                 df.at[existing_index, 'TargetPrice'] = float(target)
                 
                 # Append Updated tag to notes if not present
                 current_notes = str(df.at[existing_index, 'Notes'])
                 if "(Updated)" not in current_notes:
                     df.at[existing_index, 'Notes'] = f"{current_notes} | (Updated)"
                 elif "Manual" in current_notes:
                     pass # Already updated
                     
                 self.save_trades(df)
                 return True, "Trade updated."
            else:
                 return False, "Trade active, cannot update."

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
            "EntryDate": None, # Set ONLY when Status becomes OPEN
            "UpdatedStopLoss": None,
            "PnL": 0.0,
            "Notes": signal_data.get('Signal', 'Manual'),
            "Strategy": strategy_type,
            "ATR": atr,
            "TriggerHigh": trigger_high,
            "VWAP": vwap,
            "InitialSL": None,
            "Side": side
        }
        
        df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
        self.save_trades(df)
        return True, "Trade added successfully."

    def update_status(self):
        """
        Iterates through all active trades and updates their status based on live market data.
        """
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
                from src.utils import fetch_data_robust
                if strategy == 'Intraday':
                    start_dt = pd.to_datetime(start_date)
                    end_dt = start_dt + pd.Timedelta(days=1)
                    
                    data = fetch_data_robust(ticker, period=None, interval="1m") # Need to support start/end in utils?
                    # Utils currently only supports period/interval. Let's stick to simple downloads for now or update utils?
                    # "fetch_data_robust" signature: (ticker, period="1y", interval="1d", retries=3, delay=1)
                    # It doesn't support start/end.
                    # Let's use standard yf for intraday specific date range for now, but wrapped in try-catch in robust style?
                    # Or better, just add start/end support to util.
                    # For now, I will use yf directly for Intraday as it needs specific start/end which my util didn't implement yet.
                    # But for MTF (Daily), I can use the robust fetcher.
                    
                    data = yf.download(ticker, start=start_dt, end=end_dt, interval="1m", progress=False, auto_adjust=True)
                    
                    if data.empty: continue
                    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

                    target = row['TargetPrice']
                    sl = row['StopLoss']
                    entry = row['EntryPrice']
                    updated_sl = row.get('UpdatedStopLoss')
                    if pd.isna(updated_sl): updated_sl = None
                    
                    from src.utils import round_to_tick
                    # Ensure loaded values are clean ticks (self-healing)
                    target = round_to_tick(target)
                    sl = round_to_tick(sl)
                    entry = round_to_tick(entry)
                    if updated_sl: updated_sl = round_to_tick(updated_sl)

                    current_effective_sl = updated_sl if updated_sl is not None else sl
                    
                    # Advanced Logic Params
                    atr = row.get('ATR')
                    trigger_high = row.get('TriggerHigh')
                    
                    status_changed = False
                    
                    for timestamp, candle in data.iterrows():
                        # Convert to IST if TZ aware, else assume UTC and localize
                        if timestamp.tzinfo is None:
                            # Assume UTC if naive (common in some yf contexts or if we stripped it)
                            timestamp = timestamp.tz_localize('UTC')
                        
                        timestamp_ist = timestamp.tz_convert('Asia/Kolkata')
                        current_time = timestamp_ist.time()
                        
                        if current_time < time(9, 15): continue 
                        if current_time >= time(15, 30): break

                        high = candle['High']
                        low = candle['Low']
                        close = candle['Close']
                        
                        # --- ENTRY LOGIC ---
                        if row['Status'] == 'WAITING_ENTRY':
                            triggered = False
                            side = row.get('Side', 'BUY')
                            
                            # Standard Logic (Old)
                            if pd.isna(trigger_high): 
                                if low <= entry <= high: triggered = True
                            else:
                                # Advanced Logic with "Trigger Price"
                                # For LONG: Close > Trigger High
                                # For SHORT: Close < Trigger Low
                                
                                buffer = float(trigger_high) * 0.0005
                                
                                if side == "SELL":
                                     target_entry = float(trigger_high) - buffer # Trigger Low for short
                                     if close < target_entry:
                                         triggered = True
                                         entry = close
                                else:
                                     target_entry = float(trigger_high) + buffer
                                     if close > target_entry:
                                         triggered = True
                                         entry = close
                            
                            if triggered:
                                row['Status'] = 'OPEN'
                                row['EntryDate'] = timestamp_ist.strftime("%Y-%m-%d %H:%M:%S")
                                row['EntryPrice'] = round_to_tick(entry) 
                                
                                # --- DYNAMIC SL/TARGET CALCULATION ON ENTRY ---
                                if pd.notna(atr) and float(atr) > 0:
                                    atr_risk = 1.5 * float(atr)
                                    min_risk = entry * 0.005
                                    actual_risk = max(atr_risk, min_risk)
                                    
                                    if side == "SELL":
                                        risk_sl = entry + actual_risk
                                        t1 = entry - (2 * actual_risk) # Target below
                                    else:
                                        risk_sl = entry - actual_risk
                                        t1 = entry + (2 * actual_risk)
                                    
                                    row['StopLoss'] = round_to_tick(risk_sl)
                                    row['InitialSL'] = round_to_tick(risk_sl)
                                    row['TargetPrice'] = round_to_tick(t1)
                                    
                                    row['Notes'] = f"{row.get('Notes', '')} | Risk-Based SL/Target Set (Risk {actual_risk:.2f})"
                                    current_effective_sl = round_to_tick(risk_sl)
                                    target = round_to_tick(t1)
                                else:
                                     row['Notes'] = f"{row.get('Notes', '')} | Triggered at {timestamp.time()}"

                                status_changed = True
                                # Fallthrough

                        # --- OPEN TRADE MANAGEMENT ---
                        if row['Status'] == 'OPEN':
                            side = row.get('Side', 'BUY')
                            
                            # 1. Stop Loss Check
                            sl_hit = False
                            if side == "SELL":
                                if high >= current_effective_sl: sl_hit = True
                            else:
                                if low <= current_effective_sl: sl_hit = True
                                
                            if sl_hit:
                                row['Status'] = "STOP_LOSS_HIT"
                                row['ExitPrice'] = current_effective_sl
                                row['ExitDate'] = timestamp_ist.strftime("%Y-%m-%d %H:%M:%S")
                                
                                # PnL Logic
                                if side == "SELL":
                                    row['PnL'] = (entry - current_effective_sl) / entry * 100
                                else:
                                    row['PnL'] = (current_effective_sl - entry) / entry * 100
                                    
                                row['Notes'] = f"{row.get('Notes', '')} | SL Hit"
                                status_changed = True
                                break 

                            # 2. Target Hit logic (RRR 1:2 -> Trailing)
                            target_hit = False
                            if side == "SELL":
                                if low <= target: target_hit = True
                            else:
                                if high >= target: target_hit = True
                                
                            if target_hit:
                                if pd.isna(updated_sl) or (side == "BUY" and updated_sl < entry) or (side == "SELL" and updated_sl > entry):
                                    # First time hitting target
                                    row['UpdatedStopLoss'] = entry # Break even
                                    updated_sl = entry 
                                    current_effective_sl = entry
                                    
                                    # Extend Target
                                    initial_sl_val = row.get('InitialSL')
                                    if pd.notna(initial_sl_val):
                                         risk = abs(entry - float(initial_sl_val))
                                    else:
                                         risk = entry * 0.005
                                    
                                    if risk <= 0: risk = entry * 0.005
                                         
                                    if side == "SELL":
                                        new_target = target - risk
                                    else:
                                        new_target = target + risk
                                        
                                    row['TargetPrice'] = round_to_tick(new_target)
                                    
                                    row['Notes'] = f"{row.get('Notes', '')} | T1 Hit -> SL to BE, Target extended"
                                    status_changed = True
                                    
                                    # Check strict SL hit in same candle (Wick)
                                    sl_hit_now = False
                                    if side == "SELL":
                                        if high >= current_effective_sl: sl_hit_now = True
                                    else:
                                        if low <= current_effective_sl: sl_hit_now = True
                                        
                                    if sl_hit_now:
                                         row['Status'] = "STOP_LOSS_HIT" 
                                         row['ExitPrice'] = current_effective_sl
                                         row['ExitDate'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                         row['PnL'] = 0.0 # BE
                                         status_changed = True
                                         break
                                         
                                    target = new_target # update local var

                    # End of Day Processing
                    is_day_done = False
                    now = datetime.now()
                    signal_dt_obj = datetime.strptime(start_date, "%Y-%m-%d")
                    if signal_dt_obj.date() < now.date() or (signal_dt_obj.date() == now.date() and now.time() > time(15, 30)):
                        is_day_done = True
                    
                    if is_day_done:
                        if row['Status'] == 'WAITING_ENTRY':
                            if not status_changed:
                                row['Status'] = 'NOT_TRIGGERED'
                                row['Notes'] = f"{row.get('Notes', '')} | Expired (No Entry)"
                                status_changed = True
                        elif row['Status'] == 'OPEN':
                            if not (row['Status'] in ['STOP_LOSS_HIT', 'TARGET_HIT']): 
                                last_close = data.iloc[-1]['Close']
                                row['Status'] = 'EXIT_AT_CLOSE'
                                row['ExitPrice'] = last_close
                                row['ExitDate'] = f"{start_date} 15:30:00"
                                
                                side = row.get('Side', 'BUY')
                                if side == "SELL":
                                    row['PnL'] = (entry - last_close) / entry * 100
                                else:
                                    row['PnL'] = (last_close - entry) / entry * 100
                                    
                                row['Notes'] = f"{row.get('Notes', '')} | Auto-Squareoff"
                                status_changed = True

                    if status_changed:
                        df.loc[index] = row
                        updates_count += 1

                else:
                    # --- MTF / SWING LOGIC (PRECISION UPGRADE) ---
                    # Uses 1-Minute data for the last 5 days to capture precise execution time.
                    
                    data = None
                    try:
                        from src.utils import fetch_data_robust
                        # Fetch 5 days of 1m data
                        data = fetch_data_robust(ticker, period="5d", interval="1m")
                        
                        if data is None or data.empty:
                             # Fallback to Daily if 1m fails (captures moves older than 5 days or liquidity issues)
                             data = fetch_data_robust(ticker, period="1y", interval="1d")
                    except Exception:
                         pass
                         
                    if data is None or data.empty: continue
                    
                    target = row['TargetPrice']
                    sl = row['StopLoss']
                    entry = row['EntryPrice']
                    updated_sl = row.get('UpdatedStopLoss')
                    if pd.isna(updated_sl): updated_sl = None
                    
                    from src.utils import round_to_tick
                    target = round_to_tick(target)
                    sl = round_to_tick(sl)
                    entry = round_to_tick(entry)
                    if updated_sl: updated_sl = round_to_tick(updated_sl)
                    
                    current_effective_sl = updated_sl if updated_sl is not None else sl

                    status_changed = False
                    
                    for timestamp, candle in data.iterrows():
                        # Determine date string based on index type
                        if isinstance(timestamp, pd.Timestamp):
                            if timestamp.tzinfo is None:
                                timestamp = timestamp.tz_localize('UTC')
                            timestamp_ist = timestamp.tz_convert('Asia/Kolkata')
                            
                            current_dt_str = timestamp_ist.strftime("%Y-%m-%d")
                            exact_time_str = timestamp_ist.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            # Fallback for daily strings
                            current_dt_str = str(timestamp).split(" ")[0]
                            exact_time_str = f"{current_dt_str} 15:30:00"

                        # Date Filtering: Allow SAME DAY entry (Strict < check)
                        if current_dt_str < start_date:
                            continue
                            
                        high = candle['High']
                        low = candle['Low']
                        close = candle['Close']
                        
                        # --- ENTRY LOGIC for MTF ---
                        if row['Status'] == 'WAITING_ENTRY':
                             side = row.get('Side', 'BUY')
                             triggered = False
                             
                             if side == "SELL":
                                 if low <= entry: 
                                      triggered = True
                             else:
                                 # Standard High/Low touch check
                                 if low <= entry <= high: 
                                     triggered = True
                             
                             if triggered:
                                 row['Status'] = 'OPEN'
                                 row['EntryDate'] = exact_time_str
                                 row['Notes'] = f"{row.get('Notes', '')} | Filled at {exact_time_str}"
                                 status_changed = True
                             else:
                                 continue

                        # --- OPEN TRADE MANAGEMENT ---
                        if row['Status'] == 'OPEN':
                            side = row.get('Side', 'BUY')
                            sl_hit = False
                            target_hit = False
                            
                            # 1. Check SL
                            if side == "SELL":
                                if high >= current_effective_sl: sl_hit = True
                            else:
                                if low <= current_effective_sl: sl_hit = True
                                
                            if sl_hit:
                                row['Status'] = "STOP_LOSS_HIT"
                                row['ExitPrice'] = current_effective_sl
                                row['ExitDate'] = exact_time_str
                                
                                if side == "SELL":
                                     row['PnL'] = (entry - current_effective_sl) / entry * 100
                                else:
                                     row['PnL'] = (current_effective_sl - entry) / entry * 100
                                     
                                row['Notes'] = f"{row.get('Notes', '')} | SL Hit at {low if side=='BUY' else high}"
                                status_changed = True
                                break 
                                
                            # 2. Check Target
                            if side == "SELL":
                                if low <= target: target_hit = True
                            else:
                                if high >= target: target_hit = True
                                
                            if target_hit:
                                row['Status'] = "TARGET_HIT"
                                row['ExitPrice'] = target
                                row['ExitDate'] = timestamp_ist.strftime("%Y-%m-%d %H:%M:%S")
                                
                                if side == "SELL":
                                     row['PnL'] = (entry - target) / entry * 100
                                else:
                                     row['PnL'] = (target - entry) / entry * 100
                                     
                                row['Notes'] = f"{row.get('Notes', '')} | Target Hit at {high if side=='BUY' else low}"
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
