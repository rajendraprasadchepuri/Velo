
import yfinance as yf
import pandas as pd

def debug():
    ticker = "RELIANCE.NS"
    print(f"Downloading {ticker}...")
    df = yf.download(ticker, period='5d', interval='5m', progress=False)
    print("Columns:", df.columns)
    print("Shape:", df.shape)
    if not df.empty:
        print("Type of df['Close']:", type(df['Close']))
        print("Shape of df['Close']:", df['Close'].shape)
        print("Head of df['Close']:")
        print(df['Close'].head())

if __name__ == "__main__":
    debug()
