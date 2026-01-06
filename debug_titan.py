import yfinance as yf
import pandas as pd
from datetime import datetime

def test_titan():
    ticker = "TITAN.NS"
    start_date = "2026-01-05"
    
    print(f"Downloading {ticker} from {start_date}...")
    data = yf.download(ticker, start=start_date, progress=False, auto_adjust=True)
    
    print("\nColumns:")
    print(data.columns)
    
    print("\nData Head:")
    print(data.head())
    
    print("\nIterating:")
    if isinstance(data.columns, pd.MultiIndex):
        print("Flattening MultiIndex columns...")
        data.columns = data.columns.get_level_values(0)
        
    for date, row in data.iterrows():
        print(f"Date: {date}")
        print(f"High: {row['High']}, Low: {row['Low']}, Close: {row['Close']}")

if __name__ == "__main__":
    test_titan()
