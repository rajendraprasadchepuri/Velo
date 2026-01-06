import pandas as pd
import os
from datetime import datetime, timedelta

DATA_PATH = r"c:\Users\rajendra.chepuri\OneDrive - TTEC Digital\Documents\C_Drive\prs\git\Velo\data\live_trades.csv"

def fix_csv_timezones():
    if not os.path.exists(DATA_PATH):
        print("CSV not found.")
        return
        
    df = pd.read_csv(DATA_PATH)
    changed = False
    
    # Columns to check
    date_cols = ['EntryDate', 'ExitDate']
    
    for col in date_cols:
        if col not in df.columns: continue
        
        for idx, val in df[col].items():
            if pd.isna(val): continue
            
            try:
                # Check for "03:xx:xx" pattern or similar early morning times
                # If parsed hour < 9, it's likely UTC
                dt = pd.to_datetime(val)
                if dt.year == 2026 and dt.hour < 9:
                    # Convert: Add 5h 30m
                    new_dt = dt + timedelta(hours=5, minutes=30)
                    new_str = new_dt.strftime("%Y-%m-%d %H:%M:%S")
                    df.at[idx, col] = new_str
                    
                    # Also fix notes
                    notes = df.at[idx, 'Notes']
                    if pd.notna(notes) and str(val) in notes:
                         df.at[idx, 'Notes'] = notes.replace(str(val), new_str)
                         
                    changed = True
                    print(f"Fixed {col} row {idx}: {val} -> {new_str}")
            except Exception as e:
                pass
                
    if changed:
        df.to_csv(DATA_PATH, index=False)
        print("✅ CSV Timestamps corrected to IST.")
    else:
        print("No incorrect timestamps found.")

if __name__ == "__main__":
    fix_csv_timezones()
