import pandas as pd
from src.tracker import TradeTracker
import os

def fix_and_update():
    print("🔧 Fixing CSV Data...")
    tracker = TradeTracker()
    df = tracker.load_trades()
    
    # 1. Fix: Clear EntryDate for WAITING_ENTRY trades
    # The user manually pasted '2026-01-06' which is incorrect. It should be empty until filled.
    mask_waiting = df['Status'] == 'WAITING_ENTRY'
    df.loc[mask_waiting, 'EntryDate'] = None
    
    # Save the fix first
    tracker.save_trades(df)
    print(f"✅ Cleared EntryDate for {mask_waiting.sum()} waiting trades.")
    
    # 2. Trigger Update (This will fill EntryDate with TIMESTAMP if price matches)
    print("⏳ Running Live Status Update (Checking 1m data)...")
    updates_count = tracker.update_status()
    print(f"✅ Updated {updates_count} trades based on live market moves.")

if __name__ == "__main__":
    fix_and_update()
