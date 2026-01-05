import yfinance as yf
import pandas as pd
from ta.volatility import AverageTrueRange

def check_atr(ticker):
    print(f"\n--- Checking {ticker} ---")
    data = yf.download(ticker, period='5d', interval='5m', progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        
    atr = AverageTrueRange(high=data['High'], low=data['Low'], close=data['Close'], window=14)
    data['ATR'] = atr.average_true_range()
    
    last = data.iloc[-1]
    price = last['Close']
    atr_val = last['ATR']
    
    calc_sl_dist = 1.5 * atr_val
    calc_sl_pct = (calc_sl_dist / price) * 100
    calc_target_pct = (calc_sl_pct * 2)
    
    print(f"Price: {price:.2f}")
    print(f"5m ATR: {atr_val:.4f}")
    print(f"Risk (1.5x ATR): {calc_sl_dist:.2f} ({calc_sl_pct:.2f}%)")
    print(f"Target (2x Risk): {calc_target_pct:.2f}%")

tickers = ["TATASTEEL.NS", "RELIANCE.NS", "ADANIENT.NS"]
for t in tickers:
    check_atr(t)
