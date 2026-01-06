import yfinance as yf
import pandas as pd

if __name__ == "__main__":
    ticker = "COALINDIA.NS"
    print(f"Checking {ticker} Data for Jan 2026...")
    data = yf.download(ticker, start="2026-01-05", end="2026-01-08", progress=False, auto_adjust=True)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        
    print(data[['Open', 'High', 'Low', 'Close']])
    
    entry = 402.61
    print(f"\nEntry Target: {entry}")
    
    for date, row in data.iterrows():
        valid = row['Low'] <= entry <= row['High']
        print(f"{date.date()}: Low {row['Low']:.2f} <= {entry} <= High {row['High']:.2f} ? {'✅ YES' if valid else '❌ NO'}")
