import pandas as pd
import yfinance as yf
from datetime import datetime

# Mock trade data matches CSV
trade = {
    "Ticker": "UPL.NS",
    "SignalDate": "2026-01-05",
    "EntryPrice": 783.88,
    "StopLoss": 761.37,
    "TargetPrice": 828.89,
    "Status": "OPEN"
}

ticker = trade['Ticker']
start_date = trade['SignalDate']
target = trade['TargetPrice']
sl = trade['StopLoss']
entry = trade['EntryPrice']

print(f"Checking {ticker} from {start_date}...")
print(f"Target: {target}, SL: {sl}")

try:
    data = yf.download(ticker, start=start_date, progress=False, auto_adjust=True)
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    print("Columns:", data.columns)
    
    for date, day_data in data.iterrows():
        high = day_data['High']
        low = day_data['Low']
        
        print(f"Date: {date}, High: {high}, Low: {low}")
        
        if low <= sl:
            print("STOP LOSS HIT")
        if high >= target:
            print("TARGET HIT")
            
except Exception as e:
    print(f"Error: {e}")
