import pandas as pd
import os
from src.tracker import TradeTracker

DATA_DIR = r"c:\Users\rajendra.chepuri\OneDrive - TTEC Digital\Documents\C_Drive\prs\git\Velo\data"
LIVE_TRADES_PATH = os.path.join(DATA_DIR, "live_trades.csv")

def repair_entries():
    if not os.path.exists(LIVE_TRADES_PATH):
        print("Data file not found.")
        return

    tracker = TradeTracker()
    df = tracker.load_trades()
    
    modified_count = 0
    
    # Logic: Reset "OPEN" MTF trades that might not have filled
    for idx, row in df.iterrows():
        if row['Strategy'] == 'MTF' and row['Status'] == 'OPEN':
            # Reset to WAITING_ENTRY to force re-check
            df.at[idx, 'Status'] = 'WAITING_ENTRY'
            df.at[idx, 'EntryDate'] = None # Clear EntryDate as it wasn't validated
            
            # Clean Notes if needed
            notes = str(row['Notes'])
            if " | Filled at" in notes:
                notes = notes.split(" | Filled at")[0]
            df.at[idx, 'Notes'] = notes
            
            modified_count += 1
            
    if modified_count > 0:
        tracker.save_trades(df)
        print(f"Reset {modified_count} MTF trades to WAITING_ENTRY. Now validating...")
        
        # Trigger Update
        updates = tracker.update_status()
        print(f"Validation Complete! {updates} trades validated and updated.")
    else:
        print("No OPEN MTF trades found to repair.")

if __name__ == "__main__":
    repair_entries()
