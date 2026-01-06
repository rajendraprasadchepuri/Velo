import pandas as pd
from src.utils import fetch_data_robust

def diagnose_ticker(ticker, entry_price, signal_date_str):
    print(f"🔍 Diagnosing {ticker}...")
    print(f"   Entry Price: {entry_price}")
    print(f"   Signal Date: {signal_date_str}")
    
    # 1. Fetch 1m data
    print("   Fetching 5d 1m data...")
    data = fetch_data_robust(ticker, period="5d", interval="1m")
    
    if data is None or data.empty:
        print("   ❌ No 1m data returned.")
        return
        
    print(f"   ✅ Fetched {len(data)} candles.")
    print(f"   First Candle: {data.index[0]}")
    print(f"   Last Candle:  {data.index[-1]}")
    
    # 2. Simulate Trigger Check
    triggered = False
    trigger_time = None
    
    count_checked = 0
    for timestamp, candle in data.iterrows():
        current_date_str = timestamp.strftime("%Y-%m-%d")
        
        # Skip before signal date
        if current_date_str < signal_date_str:
            continue
            
        count_checked += 1
        high = candle['High']
        low = candle['Low']
        
        # BUY Condition: Low <= Entry <= High
        if low <= entry_price <= high:
            triggered = True
            trigger_time = timestamp
            print(f"   🎯 TARGET HIT at {timestamp}!")
            print(f"      Candle: High={high}, Low={low}, Entry={entry_price}")
            break
            
    if not triggered:
        print(f"   ⚠️ No trigger found in {count_checked} valid candles.")
        # Check proximity
        mins = data['Low'].min()
        maxs = data['High'].max()
        print(f"      Range during period: {mins} - {maxs}")
        if entry_price > maxs:
            print("      Reason: Price never reached UP to entry (if sell) or above logic issue?")
        if entry_price < mins:
             print("      Reason: Price opened and stayed ABOVE entry (Gap Up / Runaway?)")

if __name__ == "__main__":
    # Test with one of the tickers from CSV
    diagnose_ticker("ADANIPOWER.NS", 147.55, "2026-01-06")
