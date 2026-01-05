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
                
            if changed:
                df.to_csv(self.filepath, index=False)

    def load_trades(self):
        self._ensure_file_exists()
        return pd.read_csv(self.filepath)

    def save_trades(self, df):
        df.to_csv(self.filepath, index=False)

    def add_trade(self, signal_data, strategy_type="MTF", signal_date=None):
        df = self.load_trades()
        
        # Check if trade already exists for this ticker on this date to prevent duplicates
        if signal_date:
            date_str = signal_date
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        ticker = signal_data.get('Ticker')
        
        # Avoid duplicate entries for same day and strategy
        existing = df[(df['Ticker'] == ticker) & (df['SignalDate'] == date_str) & (df['Strategy'] == strategy_type)]
        
        # New Logic: Allow updating pending trades
        if not existing.empty:
            existing_index = existing.index[0]
            current_status = df.at[existing_index, 'Status']
            
            if current_status == 'WAITING_ENTRY':
                # Update existing trade with refined numbers
                df.at[existing_index, 'EntryPrice'] = float(signal_data.get('Entry Price', signal_data.get('Current Price', signal_data.get('Safe Entry', 0))))
                
                # Update SL/Target
                sl = signal_data.get('Stop Loss')
                if sl is None: sl = df.at[existing_index, 'EntryPrice'] * 0.995
                target = signal_data.get('Target Price')
                if target is None: target = df.at[existing_index, 'EntryPrice'] * 1.005
                
                df.at[existing_index, 'StopLoss'] = float(sl)
                df.at[existing_index, 'TargetPrice'] = float(target)
                df.at[existing_index, 'Notes'] = signal_data.get('Signal', 'Manual') + " (Updated)"
                
                self.save_trades(df)
                return True, "Trade updated with latest analysis."
            else:
                return False, f"Trade already active ({current_status}). Cannot overwrite."

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
            "EntryDate": None,
            "UpdatedStopLoss": None,
            "PnL": 0.0,
            "Notes": signal_data.get('Signal', 'Manual'),
            "Strategy": strategy_type
        }
        
        df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
        self.save_trades(df)
        return True, "Trade added successfully."

    def update_status(self):
        """
        Iterates through all active trades and updates their status based on live market data.
        
        Logic:
        - Intraday: Fetches 1-minute data for the Signal Date.
          - Checks 09:15-15:30 window.
          - Triggers WAITING_ENTRY -> OPEN if price crosses Entry.
          - Checks SL and Target logic on OPEN trades.
          - Handles Dynamic SL moves (Trailing) and Target Extensions.
          - Auto-squares off at 15:30 if still open.
        - MTF: Fetches daily data and checks for SL/Target hits on subsequent days.
        
        Returns:
            int: Number of trades updated.
        """
        df = self.load_trades()
        updates_count = 0
        from datetime import time
        
        for index, row in df.iterrows():
            status = row['Status']
            if status in ['STOP_LOSS_HIT', 'NOT_TRIGGERED', 'EXIT_AT_CLOSE']: # removed TARGET_HIT from ignore list to allow monitoring after hit? No, logic is different now.
                # If TARGET_HIT was final, we skip. But now we want dynamic updates, so 'TARGET_HIT' is not a final state until market close or SL hit.
                # Actually, our new logic keeps status as OPEN while updating targets.
                # So if status is OPEN, we process.
                pass
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
                    
                    data = yf.download(ticker, start=start_dt, end=end_dt, interval="1m", progress=False, auto_adjust=True)
                    
                    if data.empty: continue
                    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

                    # Filter for specific day just in case
                    # (Strictly speaking yf download with start/end handles dates, but we check times)
                    
                    target = row['TargetPrice']
                    sl = row['StopLoss']
                    entry = row['EntryPrice']
                    updated_sl = row.get('UpdatedStopLoss')
                    if pd.isna(updated_sl): updated_sl = None
                    
                    # If we have an updated SL, use that for safety check, otherwise use original SL
                    current_effective_sl = updated_sl if updated_sl is not None else sl
                    
                    status_changed = False
                    
                    for timestamp, candle in data.iterrows():
                        # Skip first 5 mins (09:15 - 09:20)
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
                                row['EntryDate'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                row['Notes'] = f"{row.get('Notes', '')} | Triggered at {timestamp.time()}"
                                status_changed = True
                                # Fallthrough to OPEN logic immediately

                        if row['Status'] == 'OPEN':
                            # Priority: SL Safety first.
                            # Use current effective SL
                            
                            if low <= current_effective_sl:
                                row['Status'] = "STOP_LOSS_HIT"
                                row['ExitPrice'] = current_effective_sl
                                row['ExitDate'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                row['PnL'] = (current_effective_sl - entry) / entry * 100
                                row['Notes'] = f"{row.get('Notes', '')} | SL Hit at {low}"
                                status_changed = True
                                break # Trade complete

                            if high >= target:
                                # Dynamic Update Logic
                                # 1. Update SL to current Target (Locked profit)
                                # 2. Increase Target by another 0.5%
                                
                                old_target = target
                                new_sl = old_target
                                new_target = old_target + (entry * 0.005) # increment by 0.5% of entry price
                                
                                row['UpdatedStopLoss'] = new_sl
                                row['TargetPrice'] = new_target
                                row['Notes'] = f"{row.get('Notes', '')} | Target {old_target} Hit -> SL moved to {new_sl}, New Target {new_target:.2f}"
                                
                                # Update local variables for next candle check (or same candle fallthrough?)
                                # Ideally we should check if new SL is hit in same candle? 
                                # If High reached target, it's possible Low also dropped below new SL in same candle?
                                # That's a "Wick" scenario. 
                                # If Low <= new_sl, then we hit target AND then stopped out at profit.
                                # Let's handle that.
                                
                                current_effective_sl = new_sl
                                target = new_target
                                status_changed = True
                                
                                if low <= current_effective_sl:
                                    # Hit target then reversed to new SL immediately
                                    row['Status'] = "STOP_LOSS_HIT" # Or "TARGET_HIT_THEN_SL"? No, just SL hit at profit.
                                    row['ExitPrice'] = current_effective_sl
                                    row['ExitDate'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                    row['PnL'] = (current_effective_sl - entry) / entry * 100
                                    row['Notes'] = f"{row.get('Notes', '')} | Reached {high} then stopped out at {current_effective_sl}"
                                    break
                                
                                # Continue monitoring
                    
                    # End of Day Processing
                    is_day_done = False
                    now = datetime.now()
                    signal_dt_obj = datetime.strptime(start_date, "%Y-%m-%d")
                    if signal_dt_obj.date() < now.date() or (signal_dt_obj.date() == now.date() and now.time() > time(15, 30)):
                        is_day_done = True
                    
                    if is_day_done:
                        if row['Status'] == 'WAITING_ENTRY':
                            # Only if NOT already triggered/changed in this loop
                            if not status_changed:
                                row['Status'] = 'NOT_TRIGGERED'
                                row['Notes'] = f"{row.get('Notes', '')} | Expired (No Entry)"
                                status_changed = True
                        elif row['Status'] == 'OPEN':
                            # Square off at close price of last candle if not stopped out
                            if not (row['Status'] in ['STOP_LOSS_HIT', 'TARGET_HIT']): # Double check
                                last_close = data.iloc[-1]['Close']
                                row['Status'] = 'EXIT_AT_CLOSE'
                                row['ExitPrice'] = last_close
                                row['ExitDate'] = start_date + " 15:30:00" # Approximate close time
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
