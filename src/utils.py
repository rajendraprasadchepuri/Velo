
import yfinance as yf
import pandas as pd
import time
import requests

def fetch_data_robust(ticker, period="1y", interval="1d", retries=3, delay=1):
    """
    Robust data fetcher with retries and validation.
    """
    for attempt in range(retries):
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
            
            # 1. Check Empty
            if df.empty:
                print(f"⚠️ Warning: {ticker} returned empty data (Attempt {attempt+1}/{retries})")
                time.sleep(delay)
                continue
                
            # 2. Handle MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            # 3. Minimum Data Validation
            if len(df) < 5: 
                print(f"⚠️ Warning: {ticker} returned insufficient data ({len(df)} rows)")
                time.sleep(delay)
                continue
                
            return df
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
             print(f"🚨 Network Error fetching {ticker}: {e}. Retrying in {delay}s...")
             time.sleep(delay)
             delay *= 2 # Exponential backoff
        except Exception as e:
             print(f"❌ Error fetching {ticker}: {e}")
             return None
             
    print(f"❌ Failed to fetch data for {ticker} after {retries} attempts.")
    return None

def calculate_position_size(entry_price, stop_loss, capital, risk_per_trade_percent=1.0):
    """
    Calculates robust position size based on Fixed Fractional Risk.
    
    Formula: 
    Risk Amount = Capital * (Risk% / 100)
    Risk Per Share = Entry - SL
    Qty = Risk Amount / Risk Per Share
    """
    try:
        entry = float(entry_price)
        sl = float(stop_loss)
        cap = float(capital)
        
        if entry <= 0 or sl <= 0 or cap <= 0: return 0, 0
        if sl >= entry: return 0, 0 # Invalid SL for Long
        
        risk_amount = cap * (risk_per_trade_percent / 100)
        risk_per_share = entry - sl
        
        if risk_per_share <= 0: return 0, 0
        
        qty = int(risk_amount / risk_per_share)
        return qty, round(risk_amount, 2)
        
    except Exception:
        return 0, 0
