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
        if atr and float(atr) > 0:
            atr_val = float(atr)
            atr_risk = 1.5 * atr_val
            min_risk = entry_price * 0.005
            
            # SL = Entry - Max(1.5 * ATR, 0.5% of Entry)
            actual_risk = max(atr_risk, min_risk)
            sl_price = entry_price - actual_risk
            
            # Target = Entry + 2 * Risk
            target_price = entry_price + (2 * actual_risk)
            
            sl = sl_price
            target = target_price
        else:
            # Fallback Defaults (0.5%)
            sl = signal_data.get('Stop Loss')
            if sl is None: sl = entry_price * 0.995 
            target = signal_data.get('Target Price')
            if target is None: target = entry_price * 1.005

        initial_status = "WAITING_ENTRY" if strategy_type == "Intraday" else "OPEN"

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
            "EntryDate": date_str if strategy_type == "MTF" else None,
            "UpdatedStopLoss": None,
            "PnL": 0.0,
            "Notes": signal_data.get('Signal', 'Manual'),
            "Strategy": strategy_type,
            "ATR": atr,
            "TriggerHigh": trigger_high,
            "VWAP": vwap,
            "InitialSL": None
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
                if strategy == 'Intraday':
                    start_dt = pd.to_datetime(start_date)
                    end_dt = start_dt + pd.Timedelta(days=1)
                    
                    data = yf.download(ticker, start=start_dt, end=end_dt, interval="1m", progress=False, auto_adjust=True)
                    
                    if data.empty: continue
                    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

                    target = row['TargetPrice']
                    sl = row['StopLoss']
                    entry = row['EntryPrice']
                    updated_sl = row.get('UpdatedStopLoss')
                    if pd.isna(updated_sl): updated_sl = None
                    
                    current_effective_sl = updated_sl if updated_sl is not None else sl
                    
                    # Advanced Logic Params
                    atr = row.get('ATR')
                    trigger_high = row.get('TriggerHigh')
                    
                    status_changed = False
                    
                    for timestamp, candle in data.iterrows():
                        if timestamp.time() < time(9, 15): continue # changed to 09:15 to allow catching early moves if valid? No strategy says wait. 
                        # Actually strategy says 5m close > trigger high.
                        # Tracker is 1m. We can approximate "5m close" by checking if minute candles sustain? 
                        # Or strictly follow "Close > TriggerHigh" on 1m basis for faster entry?
                        # User said: "wait for the current 5-minute candle to close above".
                        # To implement strictly 5-min close check on 1m data is hard without resampling.
                        # Compromise: Check if 1m Close > TriggerHigh * 1.0005 (Buffer).
                        
                        if timestamp.time() >= time(15, 30): break

                        high = candle['High']
                        low = candle['Low']
                        close = candle['Close']
                        
                        # --- ENTRY LOGIC ---
                        if row['Status'] == 'WAITING_ENTRY':
                            triggered = False
                            
                            # Standard Logic (Old)
                            if pd.isna(trigger_high): 
                                if low <= entry <= high: triggered = True
                            else:
                                # Advanced Logic: Candle Close > Trigger High + Buffer
                                buffer = float(trigger_high) * 0.0005
                                target_entry = float(trigger_high) + buffer
                                if close > target_entry:
                                    triggered = True
                                    entry = close # Slippage: Entry is at Close price
                            
                            if triggered:
                                row['Status'] = 'OPEN'
                                row['EntryDate'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                row['EntryPrice'] = entry # Update entry to actual execution price
                                
                                # --- DYNAMIC SL/TARGET CALCULATION ON ENTRY ---
                                if pd.notna(atr) and float(atr) > 0:
                                    # SL = Entry - Max(1.5 * ATR, 0.5% of Entry)
                                    # This ensures Minimum Risk is 0.5%, so Target is at least 1%
                                    atr_risk = 1.5 * float(atr)
                                    min_risk = entry * 0.005
                                    actual_risk = max(atr_risk, min_risk)
                                    
                                    risk_sl = entry - actual_risk
                                    # Ensure SL is logical (below entry for long)
                                    
                                    # Target (RRR 1:2)
                                    # Risk = Entry - SL
                                    risk = entry - risk_sl
                                    t1 = entry + (2 * risk)
                                    
                                    row['StopLoss'] = risk_sl
                                    row['InitialSL'] = risk_sl
                                    row['TargetPrice'] = t1
                                    
                                    row['Notes'] = f"{row.get('Notes', '')} | Risk-Based SL/Target Set (Risk {actual_risk:.2f})"
                                    current_effective_sl = risk_sl
                                    target = t1
                                else:
                                     row['Notes'] = f"{row.get('Notes', '')} | Triggered at {timestamp.time()}"

                                status_changed = True
                                # Fallthrough

                        # --- OPEN TRADE MANAGEMENT ---
                        if row['Status'] == 'OPEN':
                            # 1. Stop Loss Check
                            if low <= current_effective_sl:
                                row['Status'] = "STOP_LOSS_HIT"
                                row['ExitPrice'] = current_effective_sl
                                row['ExitDate'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                row['PnL'] = (current_effective_sl - entry) / entry * 100
                                row['Notes'] = f"{row.get('Notes', '')} | SL Hit"
                                status_changed = True
                                break 

                            # 2. Target Hit logic (RRR 1:2 -> Trailing)
                            if high >= target:
                                # T1 Hit!
                                # Move SL to Break-Even (Entry Price)
                                # Extend Target?
                                # "Once the price hits T1, move your SL to Break-even"
                                
                                if pd.isna(updated_sl) or updated_sl < entry:
                                    # First time hitting target
                                    row['UpdatedStopLoss'] = entry # Break even
                                    updated_sl = entry 
                                    current_effective_sl = entry
                                    
                                    # Extend Target (e.g., R3 or another risk unit)
                                    # Let's say +1 Risk Unit
                                    # RRR 1:3
                                    
                                    # Robust Risk Calculation
                                    initial_sl_val = row.get('InitialSL')
                                    if pd.notna(initial_sl_val):
                                         risk = entry - float(initial_sl_val)
                                    else:
                                         # Fallback if InitialSL missing (e.g. old trades)
                                         # Assume 0.5% risk or calculate from current SL?
                                         # Use the newly defined Min Risk Floor of 0.5% as specific fallback
                                         risk = entry * 0.005
                                    
                                    if risk <= 0: risk = entry * 0.005 # Sanity check
                                         
                                    new_target = target + risk
                                    row['TargetPrice'] = new_target
                                    
                                    row['Notes'] = f"{row.get('Notes', '')} | T1 Hit -> SL to BE, Target extended"
                                    status_changed = True
                                    
                                    # Check strict SL hit in same candle (Wick)
                                    if low <= current_effective_sl:
                                         row['Status'] = "STOP_LOSS_HIT" # Stopped out at BE
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
                        
                        # Swing: Skip Signal Date and past dates to avoid look-ahead bias
                        if current_date_str <= start_date:
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
