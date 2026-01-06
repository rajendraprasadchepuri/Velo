import yfinance as yf
import pandas as pd

def check_tz():
    ticker = "ADANIPOWER.NS"
    print(f"Fetching 1m data for {ticker}...")
    # Fetch 1 day of 1m data
    df = yf.download(ticker, period="1d", interval="1m", progress=False)
    
    if df.empty:
        print("No data.")
        return

    print("--- Timezone Info ---")
    print(f"Index TZ: {df.index.tz}")
    
    first_idx = df.index[0]
    print(f"Raw Timestamp: {first_idx}")
    print(f"Hour: {first_idx.hour}, Minute: {first_idx.minute}")
    
    # Check conversion
    try:
        ist_ts = first_idx.tz_convert('Asia/Kolkata')
        print(f"Converted to IST: {ist_ts}")
        print(f"IST Hour: {ist_ts.hour}")
    except Exception as e:
        print(f"Conversion failed: {e}")

if __name__ == "__main__":
    check_tz()
