import pandas as pd
import os
import uuid

DATA_DIR = r"c:\Users\rajendra.chepuri\OneDrive - TTEC Digital\Documents\C_Drive\prs\git\Velo\data"
LIVE_TRADES_PATH = os.path.join(DATA_DIR, "live_trades.csv")
MTF_PATH = os.path.join(DATA_DIR, "mtf_data.csv")
INTRADAY_PATH = os.path.join(DATA_DIR, "intradat_data.csv")

def import_data():
    if not os.path.exists(LIVE_TRADES_PATH):
        print("Live trades file not found!")
        return

    live_df = pd.read_csv(LIVE_TRADES_PATH)
    initial_count = len(live_df)
    
    # --- Helper to check duplicates ---
    def is_duplicate(tier, data_date, strat):
        # Check against Ticker + SignalDate + Strategy
        # Convert to string for comparison
        existing = live_df[
            (live_df['Ticker'] == tier) & 
            (live_df['SignalDate'] == pd.to_datetime(data_date).strftime('%Y-%m-%d') if pd.notnull(data_date) else data_date) & 
            (live_df['Strategy'] == strat)
        ]
        return not existing.empty

    # --- 1. Import MTF Data ---
    if os.path.exists(MTF_PATH):
        print(f"Reading {MTF_PATH}...")
        mtf_df = pd.read_csv(MTF_PATH)
        mtf_added = 0
        
        for _, row in mtf_df.iterrows():
            ticker = row.get('Ticker')
            if pd.isna(ticker): continue
            
            # Format Date
            sig_date = row.get('SignalDate')
            
            if is_duplicate(ticker, sig_date, 'MTF'):
                continue
                
            # Create new record
            entry_date = row.get('EntryDate')
            if pd.isna(entry_date): entry_date = sig_date # Default to Signal Date for MTF
            
            new_row = {
                'TradeID': row.get('TradeID') if pd.notna(row.get('TradeID')) else str(uuid.uuid4())[:8],
                'Ticker': ticker,
                'SignalDate': sig_date,
                'EntryPrice': row.get('EntryPrice'),
                'StopLoss': row.get('StopLoss'),
                'TargetPrice': row.get('TargetPrice'),
                'Status': row.get('Status', 'OPEN'),
                'ExitPrice': row.get('ExitPrice'),
                'ExitDate': row.get('ExitDate'),
                'PnL': row.get('PnL', 0),
                'Notes': row.get('Notes', 'Imported'),
                'Strategy': 'MTF',
                'EntryDate': entry_date,
                'UpdatedStopLoss': None, # New fields
                'ATR': None,
                'TriggerHigh': None,
                'VWAP': None,
                'InitialSL': None
            }
            live_df = pd.concat([live_df, pd.DataFrame([new_row])], ignore_index=True)
            mtf_added += 1
            
        print(f"Added {mtf_added} new MTF trades.")

    # --- 2. Import Intraday Data ---
    if os.path.exists(INTRADAY_PATH):
        print(f"Reading {INTRADAY_PATH}...")
        intra_df = pd.read_csv(INTRADAY_PATH)
        intra_added = 0
        
        for _, row in intra_df.iterrows():
            ticker = row.get('Ticker')
            if pd.isna(ticker): continue
            
            sig_date = row.get('SignalDate')
            
            if is_duplicate(ticker, sig_date, 'Intraday'):
                continue
            
            new_row = {
                'TradeID': row.get('TradeID') if pd.notna(row.get('TradeID')) else str(uuid.uuid4())[:8],
                'Ticker': ticker,
                'SignalDate': sig_date,
                'EntryPrice': row.get('EntryPrice'),
                'StopLoss': row.get('StopLoss'),
                'TargetPrice': row.get('TargetPrice'),
                'Status': row.get('Status', 'WAITING_ENTRY'),
                'ExitPrice': row.get('ExitPrice'),
                'ExitDate': row.get('ExitDate'),
                'PnL': row.get('PnL', 0),
                'Notes': row.get('Notes', 'Imported'),
                'Strategy': 'Intraday',
                'EntryDate': row.get('EntryDate'), # Keep original time for Intraday
                'UpdatedStopLoss': row.get('UpdatedStopLoss'),
                'ATR': None,
                'TriggerHigh': None,
                'VWAP': None,
                'InitialSL': None
            }
            
            # Map specific columns if they exist in source
            if 'Start Time' in row: new_row['EntryDate'] = row['Start Time']
            
            live_df = pd.concat([live_df, pd.DataFrame([new_row])], ignore_index=True)
            intra_added += 1
            
        print(f"Added {intra_added} new Intraday trades.")

    # Save
    if len(live_df) > initial_count:
        live_df.to_csv(LIVE_TRADES_PATH, index=False)
        print(f"Successfully saved {len(live_df) - initial_count} total new trades to live_trades.csv")
    else:
        print("No new unique trades found to import.")

if __name__ == "__main__":
    import_data()
