import pandas as pd
import numpy as np

def verify_ui_logic():
    print("Verifying UI Logic...")
    
    # Mock Data
    data = {
        "Ticker": ["A", "B", "C"],
        "SignalDate": ["2024-01-01", "2024-01-01", "2024-01-01"],
        "EntryDate": ["2024-01-01 10:00:00", None, "2024-01-01 14:30:00"],
        "ExitDate": ["2024-01-01 12:00:00", None, None],
        "EntryPrice": [100.0, 100.0, 100.0],
        "ExitPrice": [105.0, None, None],
        "PnL": [0.0, 0.0, 0.0] # Initial bad values
    }
    
    df_intra = pd.DataFrame(data)
    
    print("Original DataFrame:")
    print(df_intra)
    
    # Logic copied from Live_Performance.py
    if not df_intra.empty:
        # Format Time Columns to show only Time (HH:MM:SS) if they exist
        if 'EntryDate' in df_intra.columns:
            df_intra['EntryDate'] = pd.to_datetime(df_intra['EntryDate'], errors='coerce').dt.strftime('%H:%M:%S')
        
        if 'ExitDate' in df_intra.columns:
             # Only format if it's not None
             df_intra['ExitDate'] = pd.to_datetime(df_intra['ExitDate'], errors='coerce').dt.strftime('%H:%M:%S')
        
        # Recalculate PnL
        def calc_pnl(row):
            if pd.notnull(row['ExitPrice']) and row['ExitPrice'] > 0 and pd.notnull(row['EntryPrice']) and row['EntryPrice'] > 0:
                print(f"Calc PnL for row: Exit {row['ExitPrice']}, Entry {row['EntryPrice']}")
                return (row['ExitPrice'] - row['EntryPrice']) / row['EntryPrice'] * 100
            return row['PnL']
        
        if 'ExitPrice' in df_intra.columns and 'EntryPrice' in df_intra.columns:
            df_intra['PnL'] = df_intra.apply(calc_pnl, axis=1)

    print("\nTransformed DataFrame:")
    print(df_intra[['EntryDate', 'ExitDate', 'PnL']])
    
    # Assertions
    assert df_intra.iloc[0]['EntryDate'] == "10:00:00"
    assert df_intra.iloc[0]['ExitDate'] == "12:00:00"
    assert df_intra.iloc[0]['PnL'] == 5.0
    
    assert pd.isna(df_intra.iloc[1]['EntryDate'])
    assert pd.isna(df_intra.iloc[1]['ExitDate'])
    
    assert df_intra.iloc[2]['EntryDate'] == "14:30:00"
    assert pd.isna(df_intra.iloc[2]['ExitDate'])
    
    print("SUCCESS: Logic Verified")

if __name__ == "__main__":
    verify_ui_logic()
