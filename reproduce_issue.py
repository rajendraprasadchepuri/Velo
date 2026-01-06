import yfinance as yf
import pandas as pd
from datetime import datetime

# Test yfinance download with the problematic date
ticker = "ZOMATO.NS" # Example from screenshot (or similar)
start_date = "2026-01-05"

print(f"Dowloading {ticker} from {start_date}...")
try:
    data = yf.download(ticker, start=start_date, progress=False, auto_adjust=True)
    print("Data Downloaded:")
    print(data)
    
    for date, day_data in data.iterrows():
        print(f"Date: {date}, Index: {date}")
except Exception as e:
    print(f"Error: {e}")

# Check what happens if we download from a date that is 'tomorrow' in local time but maybe 'today' on server?
# Actually 2026-01-05 is yesterday/today. 2026-01-06 is today.
# Let's check a ticker from the screenshot.
# Row 0: Entry 3999.58. Ticker not visible but probably high value.
# Row 17: 16740.56.
# Row 13: 374.05.

# Let's try downloading for a generic ticker
data2 = yf.download("RELIANCE.NS", start="2026-01-05", progress=False)
print("Reliance Data:")
print(data2)
