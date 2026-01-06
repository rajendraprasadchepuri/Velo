import pandas as pd
import os

CSV_PATH = r"c:\Users\rajendra.chepuri\OneDrive - TTEC Digital\Documents\C_Drive\prs\git\Velo\data\live_trades.csv"

def fix_data():
    if not os.path.exists(CSV_PATH):
        print("CSV not found.")
        return

    df = pd.read_csv(CSV_PATH)
    count = 0
    updated_entry_dates = 0
    
    for index, row in df.iterrows():
        # 1. Fix Missing EntryDate for MTF
        if row['Strategy'] == 'MTF' and pd.isna(row['EntryDate']):
            df.at[index, 'EntryDate'] = row['SignalDate']
            updated_entry_dates += 1

        # 2. Fix ExitDate < SignalDate
        if pd.notna(row['ExitDate']) and pd.notna(row['SignalDate']):
            if row['ExitDate'] <= row['SignalDate']:
                print(f"Fixing Row {index}: Ticker {row['Ticker']} - Exit {row['ExitDate']} <= Signal {row['SignalDate']}")
                df.at[index, 'Status'] = 'OPEN'
                df.at[index, 'ExitPrice'] = None
                df.at[index, 'ExitDate'] = None
                df.at[index, 'PnL'] = 0.0
                # Remove "SL Hit" or "Target Hit" from notes if present? 
                # Maybe safer to leave notes but append " | Correction"
                df.at[index, 'Notes'] = str(row['Notes']) + " | Date Correction Reset"
                count += 1

    if count > 0 or updated_entry_dates > 0:
        df.to_csv(CSV_PATH, index=False)
        print(f"Fixed {count} trades with bad dates.")
        print(f"Populated {updated_entry_dates} missing EntryDates.")
    else:
        print("No issues found to fix.")

if __name__ == "__main__":
    fix_data()
