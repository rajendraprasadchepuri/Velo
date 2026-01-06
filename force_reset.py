import pandas as pd
import os
from src.tracker import TradeTracker

DATA_DIR = r"c:\Users\rajendra.chepuri\OneDrive - TTEC Digital\Documents\C_Drive\prs\git\Velo\data"
LIVE_TRADES_PATH = os.path.join(DATA_DIR, "live_trades.csv")

def force_reset_entries():
    if not os.path.exists(LIVE_TRADES_PATH):
        print("Data file not found.")
        return

    tracker = TradeTracker()
    df = tracker.load_trades()
    
    modified_count = 0
    reset_count = 0
    
    print(f"Total trades before reset: {len(df)}")
    
    # Logic: Reset ALL MTF trades from Jan 2026 batch
    for idx, row in df.iterrows():
        # Check Strategy
        if row.get('Strategy') != 'MTF':
            continue
            
        # Check Date Match (2026-01-05 or 1/5/2026)
        s_date = str(row['SignalDate'])
        is_target_batch = False
        
        if s_date.startswith('2026-01-05'): is_target_batch = True
        elif s_date.startswith('1/5/2026'): is_target_batch = True
        elif s_date.startswith('01/05/2026'): is_target_batch = True
        
        if is_target_batch:
            print(f"Resetting {row['Ticker']} (Status: {row['Status']})")
            
            df.at[idx, 'Status'] = 'WAITING_ENTRY'
            df.at[idx, 'EntryDate'] = None
            df.at[idx, 'ExitPrice'] = None
            df.at[idx, 'ExitDate'] = None
            df.at[idx, 'PnL'] = 0.0
            
            # Clean Notes: Keep only original Signal info
            notes = str(row['Notes'])
            # Split by common separators added by auto-logic
            for sep in [" | Filled", " | SL Hit", " | Target Hit", " | Auto-Squareoff"]:
                if sep in notes:
                    notes = notes.split(sep)[0]
            
            df.at[idx, 'Notes'] = notes
            reset_count += 1
            
    if reset_count > 0:
        tracker.save_trades(df)
        print(f"\n✅ Reset {reset_count} MTF trades to WAITING_ENTRY.")
        print("Now running Update Status to re-validate against strict market data...")
        
        # Trigger Update
        updates = tracker.update_status()
        print(f"\n🔄 Validation Complete! {updates} trades validated and updated.")
        
        # Verify COALINDIA specific status
        df_new = tracker.load_trades()
        coal = df_new[df_new['Ticker'] == 'COALINDIA.NS']
        if not coal.empty:
            print("\nCOALINDIA.NS Final Status:")
            print(coal[['Status', 'EntryPrice', 'SignalDate', 'Notes']])
    else:
        print("No trades matched criteria for reset.")

if __name__ == "__main__":
    force_reset_entries()
