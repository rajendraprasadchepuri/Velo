import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_PATH = os.path.join(DATA_DIR, "live_trades.csv")

if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    # Find UPL.NS and reset
    mask = (df['Ticker'] == 'UPL.NS') & (df['Status'] == 'TARGET_HIT')
    if mask.any():
        print("Resetting UPL.NS to OPEN")
        df.loc[mask, 'Status'] = 'OPEN'
        df.loc[mask, 'ExitPrice'] = None
        df.loc[mask, 'ExitDate'] = None
        df.loc[mask, 'PnL'] = 0.0
        df.to_csv(CSV_PATH, index=False)
        print("Done.")
    else:
        print("UPL.NS not found or not in TARGET_HIT status.")
else:
    print("CSV not found.")
