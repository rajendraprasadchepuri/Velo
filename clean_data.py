import pandas as pd
import os
from src.tracker import TradeTracker

DATA_DIR = r"c:\Users\rajendra.chepuri\OneDrive - TTEC Digital\Documents\C_Drive\prs\git\Velo\data"
LIVE_TRADES_PATH = os.path.join(DATA_DIR, "live_trades.csv")

def clean_data():
    if not os.path.exists(LIVE_TRADES_PATH):
        print("Data file not found.")
        return

    tracker = TradeTracker()
    df = tracker.load_trades()
    
    modified_count = 0
    
    # Logic: Reset all trades from the recent import batch (2026-01-05 onwards)
    # or any trade with suspicious ExitDate < SignalDate
    
    for idx, row in df.iterrows():
        needs_reset = False
        
        # Check 1: Exit Date before Signal Date
        if pd.notna(row['ExitDate']) and pd.notna(row['SignalDate']):
            # Robust Date Parsing
            try:
                # Handle YYYY-MM-DD format
                exit_d = pd.to_datetime(row['ExitDate']).date()
                sig_d = pd.to_datetime(row['SignalDate']).date()
                if exit_d < sig_d:
                    needs_reset = True
                    print(f"[{row['Ticker']}] Bad Date: Exit {exit_d} < Signal {sig_d}")
            except:
                pass # Ignore parse errors for now
        
        # Check 2: Suspicious Price (e.g. TITAN case)
        # Note: Hard to define generic "suspicious", but we can rely on date check 
        # for the known batch from 2026-01-05.
        
        # Check 3: Just reset the 2026-01-05 batch generally if it's closed?
        # User said "all the records seems to be incorrect".
        if str(row['SignalDate']).startswith('2026-01-05') and row['Status'] != 'OPEN':
             needs_reset = True
             print(f"[{row['Ticker']}] Resetting 2026-01-05 batch")

        if needs_reset:
            df.at[idx, 'Status'] = 'OPEN'
            df.at[idx, 'ExitPrice'] = None
            df.at[idx, 'ExitDate'] = None
            df.at[idx, 'PnL'] = 0.0
            
            # Clean Notes: Remove " | SL Hit..." or " | Target Hit..."
            notes = str(row['Notes'])
            if " | " in notes:
                # Keep only original signal note? 
                # Usually user notes are "STRONG BUY", "Manual" etc.
                # The auto notes are appended with " | ".
                # Let's strip anything after " | SL Hit" or " | Target Hit"
                # Simple heuristic: Keep first part if it looks like Signal data?
                # Actually, safe to just strip the specific bad messages if distinct
                # But easiest is: Keep everything BEFORE the first " | SL Hit" / " | Target Hit"
                
                if " | SL Hit" in notes:
                    notes = notes.split(" | SL Hit")[0]
                if " | Target Hit" in notes:
                    notes = notes.split(" | Target Hit")[0]
                if " | Auto-Squareoff" in notes:
                    notes = notes.split(" | Auto-Squareoff")[0]
                    
                df.at[idx, 'Notes'] = notes
            
            modified_count += 1
            
    if modified_count > 0:
        tracker.save_trades(df)
        print(f"Cleaned {modified_count} trades. Now refreshing status...")
        
        # Trigger Update to fetch correct data
        updates = tracker.update_status()
        print(f"Refreshed logic! {updates} trades updated with correct data.")
    else:
        print("No trades needed cleaning.")

if __name__ == "__main__":
    clean_data()
